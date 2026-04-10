import io
import sqlite3
import re
from typing import Tuple
from datetime import datetime
import unicodedata

import nextcord
from nextcord.ext import commands
from PIL import Image
from nextcord.ui import View, button
from math import ceil

from db_core import get_conn

database = get_conn()
cursor = database.cursor()



cursor.execute("""
CREATE TABLE IF NOT EXISTS names (
    user_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL COLLATE NOCASE,
    year INTEGER NOT NULL CHECK (year >= 1888),
    image_blob BLOB NOT NULL,
    image_ext TEXT NOT NULL,             -- ej: 'webp', 'png', 'jpg'
    final_score REAL NOT NULL DEFAULT 0.0,
    UNIQUE (title, year)
);""")
cursor.execute("""CREATE TABLE IF NOT EXISTS aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id INTEGER NOT NULL,
    alias TEXT NOT NULL COLLATE NOCASE,
    UNIQUE (movie_id, alias),
    FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
);""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    score REAL NOT NULL CHECK (score >= 0 AND score <= 10),
    phrase TEXT,
    UNIQUE (movie_id, user_id),
    FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES names(user_id) ON DELETE CASCADE
);""")



cursor.execute("""
CREATE TRIGGER IF NOT EXISTS trg_movies_year_not_future_ins
BEFORE INSERT ON movies
FOR EACH ROW
WHEN NEW.year > CAST(strftime('%Y','now') AS INTEGER)    -- usa el año actual
BEGIN
  SELECT RAISE(ABORT, 'Invalid year: cannot be in the future');
END;
""")
cursor.execute("""
CREATE TRIGGER IF NOT EXISTS trg_scores_after_insert
AFTER INSERT ON scores
BEGIN
    UPDATE movies
    SET final_score = COALESCE(
        (SELECT ROUND(AVG(score), 1) FROM scores WHERE movie_id = NEW.movie_id),
        0.0
    )
    WHERE id = NEW.movie_id;
END;""")
cursor.execute("""
CREATE TRIGGER IF NOT EXISTS trg_scores_after_update
AFTER UPDATE OF score ON scores
BEGIN
    UPDATE movies
    SET final_score = COALESCE(
        (SELECT ROUND(AVG(score), 1) FROM scores WHERE movie_id = NEW.movie_id),
        0.0
    )
    WHERE id = NEW.movie_id;
END;""")
cursor.execute("""
CREATE TRIGGER IF NOT EXISTS trg_scores_after_delete
AFTER DELETE ON scores
BEGIN
    UPDATE movies
    SET final_score = COALESCE(
        (SELECT ROUND(AVG(score), 1) FROM scores WHERE movie_id = OLD.movie_id),
        0.0
    )
    WHERE id = OLD.movie_id;
END;""")
cursor.execute("""
CREATE TRIGGER IF NOT EXISTS trg_alias_conflicts_with_titles
BEFORE INSERT ON aliases
FOR EACH ROW
WHEN EXISTS (
    SELECT 1 FROM movies
    WHERE LOWER(title) = LOWER(NEW.alias)
    AND id <> NEW.movie_id)
BEGIN
    SELECT RAISE(ABORT, 'Alias conflict with existing movie title');
END;""")

database.commit()


TARGET_W = 1000
TARGET_H = 1500
OUTPUT_EXT = "webp"
WEBP_QUALITY = 90

def process_image(raw_bytes: bytes) -> Tuple[bytes, str]:
    """
    Normaliza la imagen:
    - convierte a RGB (descarta alpha)
    - escala para cubrir 1000x1500 (cover)
    - centra y recorta a 1000x1500
    - guarda como WEBP con calidad WEBP_QUALITY
    Devuelve (bytes_procesados, ext)
    """
    with Image.open(io.BytesIO(raw_bytes)) as im:
        if im.mode != "RGB":
            im = im.convert("RGB")
        w, h = im.size
        scale = max(TARGET_W / w, TARGET_H / h)
        new_w = max(TARGET_W, int(round(w * scale)))
        new_h = max(TARGET_H, int(round(h * scale)))
        im = im.resize((new_w, new_h), Image.LANCZOS)
        left   = (new_w - TARGET_W) // 2
        top    = (new_h - TARGET_H) // 2
        right  = left + TARGET_W
        bottom = top + TARGET_H
        im = im.crop((left, top, right, bottom))
        out_buf = io.BytesIO()
        if OUTPUT_EXT.lower() == "webp":
            im.save(out_buf, format="WEBP", quality=WEBP_QUALITY, method=6)
        elif OUTPUT_EXT.lower() in {"jpg", "jpeg"}:
            im.save(out_buf, format="JPEG", quality=WEBP_QUALITY, optimize=True, progressive=True)
        elif OUTPUT_EXT.lower() == "png":
            im.save(out_buf, format="PNG", optimize=True)
        else:
            im.save(out_buf, format="WEBP", quality=WEBP_QUALITY, method=6)
        return out_buf.getvalue(), OUTPUT_EXT

def make_file_from_blob(image_blob: bytes, image_ext: str) -> nextcord.File:
    filename = f"poster.{image_ext.lower()}"
    return nextcord.File(io.BytesIO(image_blob), filename=filename)

def image_attachment_url(image_ext: str) -> str:
    return f"attachment://poster.{image_ext.lower()}"

def strip_accents(s):
    if s is None:
        return None
    if not isinstance(s, str):
        s = str(s)
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')

database.create_function("strip_accents", 1, strip_accents)



ITEMS_PER_PAGE = 10

class PagedEmbeds(View):
    def __init__(self, pages, author_id: int, timeout: float | None = 180):
        super().__init__(timeout=timeout)
        self.pages = pages or [nextcord.Embed(description="No results.")]
        self.index = 0
        self.author_id = author_id
        if len(self.pages) <= 1:
            for child in self.children:
                child.disabled = True

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    @button(label="⬅️", style=nextcord.ButtonStyle.secondary)
    async def prev_button(self, button, interaction: nextcord.Interaction):
        self.index = (self.index - 1) % len(self.pages)
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)

    @button(label="➡️", style=nextcord.ButtonStyle.secondary)
    async def next_button(self, button, interaction: nextcord.Interaction):
        self.index = (self.index + 1) % len(self.pages)
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)

def _split_pages_fields(fields: list[tuple[str, str]], title: str, color: nextcord.Colour) -> list[nextcord.Embed]:
    pages = []
    total_pages = max(1, ceil(len(fields) / ITEMS_PER_PAGE))
    for i in range(total_pages):
        chunk = fields[i*ITEMS_PER_PAGE:(i+1)*ITEMS_PER_PAGE]
        embed = nextcord.Embed(title=title, color=color)
        if not chunk:
            embed.description = "No results."
        else:
            for name, value in chunk:
                embed.add_field(
                    name=(name[:256] if len(name) > 256 else name),
                    value=(value[:1024] if len(value) > 1024 else value),
                    inline=False
                )
        embed.set_footer(text=f"Page {i+1}/{total_pages}")
        pages.append(embed)
    return pages

def build_list_pages_for_movies_fields(rows, title="Results", color=nextcord.Color.from_rgb(0,0,0)):
    fields = []
    for (mid, t, y, fs) in rows:
        name = f"{t} ({y})"
        value = f"Final Score: {fs:.1f} — ID: {mid}"
        fields.append((name, value))
    return _split_pages_fields(fields, title, color)

def build_list_pages_for_title_collisions_fields(rows, title, color):
    fields = []
    for r in rows:
        name = f"{r[1]} ({r[2]})"
        value = f"Final Score: {r[5]:.1f} — ID: {r[0]}"
        fields.append((name, value))
    return _split_pages_fields(fields, title, color)

def build_list_pages_for_rated_fields_def(rows, header_title, include_phrase=True, color=nextcord.Color.from_rgb(0,0,0)):
    fields = []
    for (mid, t, y, fs, sc, phr, _name) in rows:
        name = f"{t} ({y}) — ID: {mid}"
        if include_phrase and (phr or "").strip():
            value = f"Score: {sc:.1f} \"{phr}\""
        else:
            value = f"Score: {sc:.1f}"
        fields.append((name, value))
    return _split_pages_fields(fields, header_title, color)

def build_list_pages_for_rated_fields_fs(rows, header_title, include_phrase=True, color=nextcord.Color.from_rgb(0,0,0)):
    fields = []
    for (mid, t, y, fs, sc, phr, _name) in rows:
        name = f"{t} ({y})"
        value = f"Final Score: {fs:.1f} — ID: {mid}"
        fields.append((name, value))
    return _split_pages_fields(fields, header_title, color)

def build_list_pages_for_movies_with_user_score_fields(rows, title="Results", color=nextcord.Color.from_rgb(0,0,0)):
    fields = []
    for (mid, t, y, fs, us) in rows:
        name = f"{t} ({y})"
        if us is not None:
            value = f"Score: {us:.1f} — ID: {mid}"
        else:
            value = f"Final Score: {fs:.1f} — ID: {mid}"
        fields.append((name, value))
    return _split_pages_fields(fields, title, color)




class db_ratings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = get_conn()
        self.cursor = self.db.cursor()



    @nextcord.slash_command(name="name")
    async def name(self,
                   interaction: nextcord.Interaction,
                   name: str = nextcord.SlashOption(description="Your display name", required=True)):
        await interaction.response.defer(ephemeral=False)
        try:
            cursor.execute("SELECT * FROM names WHERE user_id = ?", (interaction.user.id,))
            if cursor.fetchone():
                cursor.execute("UPDATE names SET name = ? WHERE user_id = ?", (name, interaction.user.id))
            else:
                cursor.execute("INSERT INTO names (user_id, name) VALUES (?, ?)", (interaction.user.id, name))
            database.commit()
            await interaction.followup.send(f"Your display name has been set to: {name}")
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")



    @nextcord.slash_command(name="add")
    async def add(self,
                  interaction: nextcord.Interaction,
                  title: str = nextcord.SlashOption(description="Movie title", required=True),
                  year: int = nextcord.SlashOption(description="Movie release year", required=True),
                  image: nextcord.Attachment = nextcord.SlashOption(description="Movie poster", required=True),
                  other_title_1: str = nextcord.SlashOption(description="Other titles", required=False, default=None),
                  other_title_2: str = nextcord.SlashOption(description="Other titles", required=False, default=None),
                  other_title_3: str = nextcord.SlashOption(description="Other titles", required=False, default=None)):
        await interaction.response.defer(ephemeral=False)
        try:
            raw = await image.read()
            img_bytes, img_ext = process_image(raw)
            cursor.execute("INSERT INTO movies (title, year, image_blob, image_ext) VALUES (?, ?, ?, ?)", (title, year, img_bytes, img_ext))
            database.commit()
            cursor.execute("SELECT id, title, year, image_blob, image_ext FROM movies WHERE title = ? AND year = ?", (title, year))
            movie = cursor.fetchone()
            for other_title in (other_title_1, other_title_2, other_title_3):
                if other_title:
                    if other_title.lower() == title.lower():
                        continue
                    cursor.execute("INSERT INTO aliases (movie_id, alias) VALUES (?, ?)", (movie[0], other_title))
                    database.commit()
            cursor.execute("SELECT alias FROM aliases WHERE movie_id = ? ORDER BY alias ASC", (movie[0],))
            aliases = [row[0] for row in cursor.fetchall()]
            desc = ""
            if aliases:
                desc = "Other Titles: " + ", ".join(aliases)
            embed = nextcord.Embed(title=f"{movie[1]} ({movie[2]})", description=desc, color=nextcord.Color.from_rgb(0, 255, 0))
            file = make_file_from_blob(movie[3], movie[4])
            embed.set_image(url=image_attachment_url(movie[4]))
            embed.set_footer(text=f"ID: {movie[0]}")
            if other_title_1 and other_title_1.lower() == title.lower() or \
               other_title_2 and other_title_2.lower() == title.lower() or \
               other_title_3 and other_title_3.lower() == title.lower():
                await interaction.followup.send(f"Movie {movie[1]} ({movie[2]}) added to the database", embed=embed, file=file)
                return
            await interaction.followup.send(f"Movie {movie[1]} ({movie[2]}) added to the database", embed=embed, file=file)
        except sqlite3.IntegrityError:
            if year > datetime.now().year:
                await interaction.followup.send("Invalid year: cannot be in the future.")
                return
            elif year < 1888:
                await interaction.followup.send("Invalid year: must be 1888 or later.")
                return
            await interaction.followup.send(f"Movie {title} ({year}) already exists in the database.")
            return None
        except ValueError as ve:
            await interaction.followup.send(f"Image error: {ve}")
            return None
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")
            return None



    @nextcord.slash_command(name="show")
    async def show(self,
                   interaction: nextcord.Interaction,
                   id: int = nextcord.SlashOption(description="Movie ID", required=False, default=None),
                   title: str = nextcord.SlashOption(description="Movie title", required=False, default=None),
                   year: int = nextcord.SlashOption(description="Movie release year", required=False, default=None)):
        await interaction.response.defer(ephemeral=False)
        try:
            if not id and not title and not year: # ninguno
                await interaction.followup.send("Please provide at least one search parameter.")
                return
            if id and not title and not year: # id
                cursor.execute("SELECT id, title, year, image_blob, image_ext, final_score FROM movies WHERE id = ?", (id,))
                rows = cursor.fetchall()
                if not rows:
                    await interaction.followup.send(f"Movie (ID: {id}) not found.")
                    return
            elif not id and year and not title: # year
                cursor.execute("SELECT id, title, year, image_blob, image_ext, final_score FROM movies WHERE year = ?", (year,))
                rows = cursor.fetchall()
                if not rows:
                    await interaction.followup.send(f"Movies from year {year} not found.")
                    return
                if len(rows) > 1:
                    pages = build_list_pages_for_title_collisions_fields(
                        rows,
                        title=f"Multiple {year} Movies:",
                        color=nextcord.Color.from_rgb(0, 0, 0)
                    )
                    view = PagedEmbeds(pages, author_id=interaction.user.id)
                    await interaction.followup.send(embed=pages[0], view=view)
                    return
            elif not id and title and not year: # title
                cursor.execute("""SELECT DISTINCT m.id, m.title, m.year, m.image_blob, m.image_ext, m.final_score
                                FROM movies m
                                LEFT JOIN aliases a ON m.id = a.movie_id
                                WHERE LOWER(strip_accents(COALESCE(m.title, ''))) = LOWER(strip_accents(?)) OR LOWER(strip_accents(COALESCE(a.alias, ''))) = LOWER(strip_accents(?))""", (title, title))
                rows = cursor.fetchall()
                if not rows:
                    await interaction.followup.send(f"Movie {title} not found.")
                    return
                if len(rows) > 1:
                    pages = build_list_pages_for_title_collisions_fields(
                        rows,
                        title=f"Multiple Movies Called {title}:",
                        color=nextcord.Color.from_rgb(0, 0, 0)
                    )
                    view = PagedEmbeds(pages, author_id=interaction.user.id)
                    await interaction.followup.send(embed=pages[0], view=view)
                    return
            elif id and title and not year: # id, title
                cursor.execute("""SELECT DISTINCT m.id, m.title, m.year, m.image_blob, m.image_ext, m.final_score
                                FROM movies m LEFT JOIN aliases a ON m.id = a.movie_id
                                WHERE m.id = ? AND (LOWER(strip_accents(COALESCE(m.title, ''))) = LOWER(strip_accents(?)) OR LOWER(strip_accents(COALESCE(a.alias, ''))) = LOWER(strip_accents(?)))""",
                            (id, title, title))
                rows = cursor.fetchall()
                if not rows:
                    cursor.execute("""SELECT DISTINCT id, title, year, image_blob, image_ext, final_score
                                    FROM movies
                                    WHERE id = ?""",
                                (id,))
                    rows = cursor.fetchall()
                    cursor.execute("""SELECT DISTINCT m.id, m.title, m.year, m.image_blob, m.image_ext, m.final_score
                                    FROM movies m LEFT JOIN aliases a ON m.id = a.movie_id
                                    WHERE (LOWER(strip_accents(COALESCE(m.title, ''))) = LOWER(strip_accents(?)) OR LOWER(strip_accents(COALESCE(a.alias, ''))) = LOWER(strip_accents(?)))""",
                                (title, title))
                    if not rows:
                        rows = cursor.fetchall()
                    else:
                        rows.extend(cursor.fetchall())
                    if not rows:
                        await interaction.followup.send(f"No movies called {title} or ID: {id} found.")
                        return
                    if len(rows) > 1:
                        pages = build_list_pages_for_title_collisions_fields(
                            rows,
                            title=f"All Movies Called {title} or ID: {id}:",
                            color=nextcord.Color.from_rgb(0, 0, 0)
                        )
                        view = PagedEmbeds(pages, author_id=interaction.user.id)
                        await interaction.followup.send(embed=pages[0], view=view)
                        return
            elif id and not title and year: # id, year
                cursor.execute("""SELECT id, title, year, image_blob, image_ext, final_score FROM movies
                                WHERE id = ? AND year = ?""", (id, year))
                rows = cursor.fetchall()
                if not rows:
                    cursor.execute("""SELECT DISTINCT id, title, year, image_blob, image_ext, final_score
                                    FROM movies
                                    WHERE id = ?""",
                                (id,))
                    rows = cursor.fetchall()
                    cursor.execute("""SELECT DISTINCT id, title, year, image_blob, image_ext, final_score
                                    FROM movies
                                    WHERE year = ?""",
                                (year,))
                    if not rows:
                        rows = cursor.fetchall()
                    else:
                        rows.extend(cursor.fetchall())
                    if not rows:
                        await interaction.followup.send(f"No movies from {year} or ID: {id} found.")
                        return
                    if len(rows) > 1:
                        pages = build_list_pages_for_title_collisions_fields(
                            rows,
                            title=f"All Movies From {year} or ID: {id}:",
                            color=nextcord.Color.from_rgb(0, 0, 0)
                        )
                        view = PagedEmbeds(pages, author_id=interaction.user.id)
                        await interaction.followup.send(embed=pages[0], view=view)
                        return
            elif not id and title and year: # title, year
                cursor.execute("""SELECT DISTINCT m.id, m.title, m.year, m.image_blob, m.image_ext, m.final_score
                                FROM movies m
                                LEFT JOIN aliases a ON m.id = a.movie_id
                                WHERE (LOWER(strip_accents(COALESCE(m.title, ''))) = LOWER(strip_accents(?)) OR LOWER(strip_accents(COALESCE(a.alias, ''))) = LOWER(strip_accents(?))) AND m.year = ?""",
                            (title, title, year))
                rows = cursor.fetchall()
                if not rows:
                    cursor.execute("""SELECT DISTINCT m.id, m.title, m.year, m.image_blob, m.image_ext, m.final_score
                                    FROM movies m LEFT JOIN aliases a ON m.id = a.movie_id
                                    WHERE (LOWER(strip_accents(COALESCE(m.title, ''))) = LOWER(strip_accents(?)) OR LOWER(strip_accents(COALESCE(a.alias, ''))) = LOWER(strip_accents(?)))""",
                                (title, title))
                    rows = cursor.fetchall()
                    cursor.execute("""SELECT DISTINCT id, title, year, image_blob, image_ext, final_score
                                    FROM movies
                                    WHERE year = ?""",
                                (year,))
                    if not rows:
                        rows = cursor.fetchall()
                    else:
                        rows.extend(cursor.fetchall())
                    if not rows:
                        await interaction.followup.send(f"No movies called {title} or from {year} found.")
                        return
                    if len(rows) > 1:
                        pages = build_list_pages_for_title_collisions_fields(
                            rows,
                            title=f"All Movies Called {title} or From {year}:",
                            color=nextcord.Color.from_rgb(0, 0, 0)
                        )
                        view = PagedEmbeds(pages, author_id=interaction.user.id)
                        await interaction.followup.send(embed=pages[0], view=view)
                        return
            else:  # id, title, year
                cursor.execute("""SELECT DISTINCT m.id, m.title, m.year, m.image_blob, m.image_ext, m.final_score
                                FROM movies m LEFT JOIN aliases a ON m.id = a.movie_id
                                WHERE m.id = ? AND (LOWER(strip_accents(COALESCE(m.title, ''))) = LOWER(strip_accents(?)) OR LOWER(strip_accents(COALESCE(a.alias, ''))) = LOWER(strip_accents(?))) AND m.year = ?""",
                            (id, title, title, year))
                rows = cursor.fetchall()
                if not rows:
                    cursor.execute("""SELECT DISTINCT id, title, year, image_blob, image_ext, final_score
                                    FROM movies
                                    WHERE id = ?""",
                                (id,))
                    rows = cursor.fetchall()
                    cursor.execute("""SELECT DISTINCT m.id, m.title, m.year, m.image_blob, m.image_ext, m.final_score
                                    FROM movies m LEFT JOIN aliases a ON m.id = a.movie_id
                                    WHERE (LOWER(strip_accents(COALESCE(m.title, ''))) = LOWER(strip_accents(?)) OR LOWER(strip_accents(COALESCE(a.alias, ''))) = LOWER(strip_accents(?)))""",
                                (title, title))
                    rowsb = cursor.fetchall()
                    cursor.execute("""SELECT DISTINCT id, title, year, image_blob, image_ext, final_score
                                    FROM movies
                                    WHERE year = ?""",
                                (year,))
                    rowsc = cursor.fetchall()
                    if not rows:
                        rows = rowsb
                    else:
                        rows.extend(rowsb)
                    if not rows:
                        rows = rowsc
                    else:
                        rows.extend(rowsc)
                    if not rows:
                        await interaction.followup.send(f"No movies called {title}, from {year}, or ID: {id} found.")
                        return
                    if len(rows) > 1:
                        pages = build_list_pages_for_title_collisions_fields(
                            rows,
                            title=f"All Movies Called {title}, From {year}, or ID: {id}:",
                            color=nextcord.Color.from_rgb(0, 0, 0)
                        )
                        view = PagedEmbeds(pages, author_id=interaction.user.id)
                        await interaction.followup.send(embed=pages[0], view=view)
                        return
            movie = rows[0]
            cursor.execute("SELECT alias FROM aliases WHERE movie_id = ? ORDER BY alias ASC", (movie[0],))
            aliases = [row[0] for row in cursor.fetchall()]
            desc = ""
            if aliases:
                desc = "Other Titles: " + ", ".join(aliases)
            cursor.execute("""SELECT n.name, s.user_id, s.score, s.phrase
                            FROM scores s
                            LEFT JOIN names n ON s.user_id = n.user_id
                            WHERE s.movie_id = ?
                            ORDER BY n.name ASC, s.user_id ASC""", (movie[0],))
            ratings = cursor.fetchall()
            rating_lines = []
            for name, uid, score, phrase in ratings:
                display = name
                if not display:
                    try:
                        user = await interaction.client.fetch_user(uid)
                        display = getattr(user, "global_name", None) or user.name
                    except Exception:
                        display = str(uid)
                phrase = phrase or ""
                if phrase:
                    rating_lines.append(f'- {display}: {score:.1f}/10 "{phrase}"')
                else:
                    rating_lines.append(f'- {display}: {score:.1f}/10')
            embed = nextcord.Embed(
                title=f"{movie[1]} ({movie[2]})",
                description=desc or None,
                color=nextcord.Color.from_rgb(0, 0, 255)
            )
            if rating_lines:
                embed.add_field(name="Scores:", value="\n".join(rating_lines), inline=False)
            file = make_file_from_blob(movie[3], movie[4])
            embed.set_image(url=image_attachment_url(movie[4]))
            if movie[5] > 0:
                embed.set_footer(text=f"Final Score: {movie[5]:.1f}/10 - ID: {movie[0]}")
            else:
                embed.set_footer(text=f"ID: {movie[0]}")
            await interaction.followup.send(embed=embed, file=file)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")
            return None



    @nextcord.slash_command(name="edit")
    async def edit(self,
                   interaction: nextcord.Interaction,
                   id: int = nextcord.SlashOption(description="Movie ID", required=True),
                   title: str = nextcord.SlashOption(description="New movie title", required=False, default=None),
                   year: int = nextcord.SlashOption(description="New movie release year", required=False, default=None),
                   image: nextcord.Attachment = nextcord.SlashOption(description="New movie poster", required=False, default=None),
                   other_title: str = nextcord.SlashOption(description="Other titles", required=False, default=None),
                   delete_title: str = nextcord.SlashOption(description="Delete other titles", required=False, default=None)):
        await interaction.response.defer(ephemeral=False)
        try:
            cursor.execute("SELECT id, title, year, image_blob, image_ext, final_score FROM movies WHERE id = ?", (id,))
            movie = cursor.fetchone()
            if not movie:
                await interaction.followup.send(f"Movie (ID: {id}) not found.")
                return
            try:
                if not title and not year and not image and not other_title and not delete_title:
                    await interaction.followup.send("No changes provided.")
                    return
                if title:
                    cursor.execute("SELECT alias FROM aliases WHERE movie_id = ?", (id,))
                    existing_aliases = {a for (a,) in cursor.fetchall()}
                    if title == movie[1]:
                        await interaction.followup.send("New title is the same as the current title.")
                        return
                    if title in existing_aliases:
                        await interaction.followup.send("New title cannot be the same as an existing alias.")
                        return
                    cursor.execute("UPDATE movies SET title = ? WHERE id = ?", (title, id))
                if year:
                    if year > datetime.now().year:
                        await interaction.followup.send(f"Cannot update year to a future year.")
                        return
                    cursor.execute("UPDATE movies SET year = ? WHERE id = ?", (year, id))
                if image:
                    raw = await image.read()
                    img_bytes, img_ext = process_image(raw)
                    cursor.execute("UPDATE movies SET image_blob = ?, image_ext = ? WHERE id = ?", (img_bytes, img_ext, id))
                if other_title:
                    if other_title == title or other_title == movie[1]:
                        await interaction.followup.send("Other titles cannot be the same as the movie title.")
                        return
                    cursor.execute("INSERT INTO aliases (movie_id, alias) VALUES (?, ?)", (id, other_title))
                if delete_title:
                    cursor.execute("DELETE FROM aliases WHERE movie_id = ? AND alias = ?", (id, delete_title))
                database.commit()
                cursor.execute("""SELECT id, title, year, image_blob, image_ext, final_score FROM movies
                                WHERE id = ?""", (id,))
                movie = cursor.fetchone()
                cursor.execute("SELECT alias FROM aliases WHERE movie_id = ? ORDER BY alias ASC", (movie[0],))
                aliases = [row[0] for row in cursor.fetchall()]
                desc = ""
                if aliases:
                    desc = "Other Titles: " + ", ".join(aliases)
                cursor.execute("""SELECT n.name, s.user_id, s.score, s.phrase
                                FROM scores s
                                LEFT JOIN names n ON s.user_id = n.user_id
                                WHERE s.movie_id = ?
                                ORDER BY n.name ASC, s.user_id ASC""", (movie[0],))
                ratings = cursor.fetchall()
                rating_lines = []
                for name, uid, score, phrase in ratings:
                    display = name
                    if not display:
                        try:
                            user = await interaction.client.fetch_user(uid)
                            display = getattr(user, "global_name", None) or user.name
                        except Exception:
                            display = str(uid)
                    phrase = phrase or ""
                    if phrase:
                        rating_lines.append(f'- {display}: {score:.1f}/10 "{phrase}"')
                    else:
                        rating_lines.append(f'- {display}: {score:.1f}/10')
                embed = nextcord.Embed(
                    title=f"{movie[1]} ({movie[2]})",
                    description=desc or None,
                    color=nextcord.Color.from_rgb(0, 0, 255)
                )
                if rating_lines:
                    embed.add_field(name="Scores:", value="\n".join(rating_lines), inline=False)
                file = make_file_from_blob(movie[3], movie[4])
                embed.set_image(url=image_attachment_url(movie[4]))
                if movie[5] > 0:
                    embed.set_footer(text=f"Final Score: {movie[5]:.1f}/10 - ID: {movie[0]}")
                else:
                    embed.set_footer(text=f"ID: {movie[0]}")
                await interaction.followup.send(embed=embed, file=file)
            except sqlite3.IntegrityError as e:
                await interaction.followup.send(f"Update failed: {e}")
            except ValueError as ve:
                await interaction.followup.send(f"Image error: {ve}")
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")
            return None



    @nextcord.slash_command(name="rate")
    async def rate(self,
                   interaction: nextcord.Interaction,
                   id: int = nextcord.SlashOption(description="Movie ID", required=False, default=None),
                   title: str = nextcord.SlashOption(description="Movie title", required=False, default=None),
                   year: int = nextcord.SlashOption(description="Movie release year", required=False, default=None),
                   score: str = nextcord.SlashOption(description="Rating score", required=False, default=None),
                   phrase: str = nextcord.SlashOption(description="Rating phrase", required=False, default="")):
        await interaction.response.defer(ephemeral=False)
        try:
            funca = True
            if not id and not title and not year: # ninguno
                await interaction.followup.send("Please provide at least one search parameter.")
                return
            if id and not title and not year: # id
                cursor.execute("SELECT id, title, year, image_blob, image_ext, final_score FROM movies WHERE id = ?", (id,))
                rows = cursor.fetchall()
                if not rows:
                    await interaction.followup.send(f"Movie (ID: {id}) not found.")
                    return
            elif not id and year and not title: # year
                funca = False
                cursor.execute("SELECT id, title, year, image_blob, image_ext, final_score FROM movies WHERE year = ?", (year,))
                rows = cursor.fetchall()
                if not rows:
                    await interaction.followup.send(f"Movies from year {year} not found.")
                    return
                if len(rows) > 1:
                    pages = build_list_pages_for_title_collisions_fields(
                        rows,
                        title=f"Multiple {year} Movies:",
                        color=nextcord.Color.from_rgb(0, 0, 0)
                    )
                    view = PagedEmbeds(pages, author_id=interaction.user.id)
                    await interaction.followup.send(embed=pages[0], view=view)
                    return
            elif not id and title and not year: # title
                cursor.execute("""SELECT DISTINCT m.id, m.title, m.year, m.image_blob, m.image_ext, m.final_score
                                FROM movies m
                                LEFT JOIN aliases a ON m.id = a.movie_id
                                WHERE LOWER(strip_accents(COALESCE(m.title, ''))) = LOWER(strip_accents(?)) OR LOWER(strip_accents(COALESCE(a.alias, ''))) = LOWER(strip_accents(?))""", (title, title))
                rows = cursor.fetchall()
                if not rows:
                    await interaction.followup.send(f"Movie {title} not found.")
                    return
                if len(rows) > 1:
                    pages = build_list_pages_for_title_collisions_fields(
                        rows,
                        title=f"Multiple Movies Called {title}:",
                        color=nextcord.Color.from_rgb(0, 0, 0)
                    )
                    view = PagedEmbeds(pages, author_id=interaction.user.id)
                    await interaction.followup.send(embed=pages[0], view=view)
                    return
            elif id and title and not year: # id, title
                cursor.execute("""SELECT DISTINCT m.id, m.title, m.year, m.image_blob, m.image_ext, m.final_score
                                FROM movies m LEFT JOIN aliases a ON m.id = a.movie_id
                                WHERE m.id = ? AND (LOWER(strip_accents(COALESCE(m.title, ''))) = LOWER(strip_accents(?)) OR LOWER(strip_accents(COALESCE(a.alias, ''))) = LOWER(strip_accents(?)))""",
                            (id, title, title))
                rows = cursor.fetchall()
                if not rows:
                    funca = False
                    cursor.execute("""SELECT DISTINCT id, title, year, image_blob, image_ext, final_score
                                    FROM movies
                                    WHERE id = ?""",
                                (id,))
                    rows = cursor.fetchall()
                    cursor.execute("""SELECT DISTINCT m.id, m.title, m.year, m.image_blob, m.image_ext, m.final_score
                                    FROM movies m LEFT JOIN aliases a ON m.id = a.movie_id
                                    WHERE (LOWER(strip_accents(COALESCE(m.title, ''))) = LOWER(strip_accents(?)) OR LOWER(strip_accents(COALESCE(a.alias, ''))) = LOWER(strip_accents(?)))""",
                                (title, title))
                    if not rows:
                        rows = cursor.fetchall()
                    else:
                        rows.extend(cursor.fetchall())
                    if not rows:
                        await interaction.followup.send(f"No movies called {title} or ID: {id} found.")
                        return
                    if len(rows) > 1:
                        pages = build_list_pages_for_title_collisions_fields(
                            rows,
                            title=f"All Movies Called {title} or ID: {id}:",
                            color=nextcord.Color.from_rgb(0, 0, 0)
                        )
                        view = PagedEmbeds(pages, author_id=interaction.user.id)
                        await interaction.followup.send(embed=pages[0], view=view)
                        return
            elif id and not title and year: # id, year
                cursor.execute("""SELECT id, title, year, image_blob, image_ext, final_score FROM movies
                                WHERE id = ? AND year = ?""", (id, year))
                rows = cursor.fetchall()
                if not rows:
                    funca = False
                    cursor.execute("""SELECT DISTINCT id, title, year, image_blob, image_ext, final_score
                                    FROM movies
                                    WHERE id = ?""",
                                (id,))
                    rows = cursor.fetchall()
                    cursor.execute("""SELECT DISTINCT id, title, year, image_blob, image_ext, final_score
                                    FROM movies
                                    WHERE year = ?""",
                                (year,))
                    if not rows:
                        rows = cursor.fetchall()
                    else:
                        rows.extend(cursor.fetchall())
                    if not rows:
                        await interaction.followup.send(f"No movies from {year} or ID: {id} found.")
                        return
                    if len(rows) > 1:
                        pages = build_list_pages_for_title_collisions_fields(
                            rows,
                            title=f"All Movies From {year} or ID: {id}:",
                            color=nextcord.Color.from_rgb(0, 0, 0)
                        )
                        view = PagedEmbeds(pages, author_id=interaction.user.id)
                        await interaction.followup.send(embed=pages[0], view=view)
                        return
            elif not id and title and year: # title, year
                cursor.execute("""SELECT DISTINCT m.id, m.title, m.year, m.image_blob, m.image_ext, m.final_score
                                FROM movies m
                                LEFT JOIN aliases a ON m.id = a.movie_id
                                WHERE (LOWER(strip_accents(COALESCE(m.title, ''))) = LOWER(strip_accents(?)) OR LOWER(strip_accents(COALESCE(a.alias, ''))) = LOWER(strip_accents(?))) AND m.year = ?""",
                            (title, title, year))
                rows = cursor.fetchall()
                if not rows:
                    funca = False
                    cursor.execute("""SELECT DISTINCT m.id, m.title, m.year, m.image_blob, m.image_ext, m.final_score
                                    FROM movies m LEFT JOIN aliases a ON m.id = a.movie_id
                                    WHERE (LOWER(strip_accents(COALESCE(m.title, ''))) = LOWER(strip_accents(?)) OR LOWER(strip_accents(COALESCE(a.alias, ''))) = LOWER(strip_accents(?)))""",
                                (title, title))
                    rows = cursor.fetchall()
                    cursor.execute("""SELECT DISTINCT id, title, year, image_blob, image_ext, final_score
                                    FROM movies
                                    WHERE year = ?""",
                                (year,))
                    if not rows:
                        rows = cursor.fetchall()
                    else:
                        rows.extend(cursor.fetchall())
                    if not rows:
                        await interaction.followup.send(f"No movies called {title} or from {year} found.")
                        return
                    if len(rows) > 1:
                        pages = build_list_pages_for_title_collisions_fields(
                            rows,
                            title=f"All Movies Called {title} or From {year}:",
                            color=nextcord.Color.from_rgb(0, 0, 0)
                        )
                        view = PagedEmbeds(pages, author_id=interaction.user.id)
                        await interaction.followup.send(embed=pages[0], view=view)
                        return
            else:  # id, title, year
                cursor.execute("""SELECT DISTINCT m.id, m.title, m.year, m.image_blob, m.image_ext, m.final_score
                                FROM movies m LEFT JOIN aliases a ON m.id = a.movie_id
                                WHERE m.id = ? AND (LOWER(strip_accents(COALESCE(m.title, ''))) = LOWER(strip_accents(?)) OR LOWER(strip_accents(COALESCE(a.alias, ''))) = LOWER(strip_accents(?))) AND m.year = ?""",
                            (id, title, title, year))
                rows = cursor.fetchall()
                if not rows:
                    funca = False
                    cursor.execute("""SELECT DISTINCT id, title, year, image_blob, image_ext, final_score
                                    FROM movies
                                    WHERE id = ?""",
                                (id,))
                    rows = cursor.fetchall()
                    cursor.execute("""SELECT DISTINCT m.id, m.title, m.year, m.image_blob, m.image_ext, m.final_score
                                    FROM movies m LEFT JOIN aliases a ON m.id = a.movie_id
                                    WHERE (LOWER(strip_accents(COALESCE(m.title, ''))) = LOWER(strip_accents(?)) OR LOWER(strip_accents(COALESCE(a.alias, ''))) = LOWER(strip_accents(?)))""",
                                (title, title))
                    rowsb = cursor.fetchall()
                    cursor.execute("""SELECT DISTINCT id, title, year, image_blob, image_ext, final_score
                                    FROM movies
                                    WHERE year = ?""",
                                (year,))
                    rowsc = cursor.fetchall()
                    if not rows:
                        rows = rowsb
                    else:
                        rows.extend(rowsb)
                    if not rows:
                        rows = rowsc
                    else:
                        rows.extend(rowsc)
                    if not rows:
                        await interaction.followup.send(f"No movies called {title}, from {year}, or ID: {id} found.")
                        return
                    if len(rows) > 1:
                        pages = build_list_pages_for_title_collisions_fields(
                            rows,
                            title=f"All Movies Called {title}, From {year}, or ID: {id}:",
                            color=nextcord.Color.from_rgb(0, 0, 0)
                        )
                        view = PagedEmbeds(pages, author_id=interaction.user.id)
                        await interaction.followup.send(embed=pages[0], view=view)
                        return
            if not score and not phrase:
                await interaction.followup.send("Please provide at least a score or a phrase to rate the movie.")
                return
            score_val = None
            if score:
                score_text = score.strip().replace(",", ".")
                if not re.fullmatch(r'^(?:10(?:\.0)?|[0-9](?:\.[0-9])?)$', score_text):
                    await interaction.followup.send(
                        "Puntaje inválido. Usa un número entre 1 y 10 con **máximo un decimal** (p. ej. 7.5 o 7,5), "
                        "o **0** para eliminar tu puntaje."
                    )
                score_val = float(score_text)
                if (score_val < 0 or score_val > 10) or (0 < score_val < 1):
                    await interaction.followup.send("Invalid score. Please provide a score between 1 and 10, or 0 to remove.")
                    return
            movie = rows[0]
            if not movie:
                await interaction.followup.send(f"Movie {title} ({year}) not found.")
                return
            if funca == True:
                if score:
                    if score_val == 0:
                        cursor.execute("""DELETE FROM scores WHERE movie_id = ? AND user_id = ?""",
                                    (movie[0], interaction.user.id))
                        database.commit()
                        await interaction.followup.send(f"Movie {movie[1]} ({movie[2]}) rating removed.")
                        return
                display_name = (getattr(interaction.user, "global_name", None) or
                                interaction.user.display_name or interaction.user.name)
                cursor.execute("INSERT OR IGNORE INTO names (user_id, name) VALUES (?, ?)",
                            (interaction.user.id, display_name))
                try:
                    cursor.execute("""INSERT INTO scores (movie_id, user_id, score, phrase) VALUES (?, ?, ?, ?)""",
                                (movie[0], interaction.user.id, score_val, phrase))
                    database.commit()
                except sqlite3.IntegrityError:
                    if not score:
                        row = cursor.execute("""SELECT score FROM scores WHERE movie_id = ? AND user_id = ?""",
                                    (movie[0], interaction.user.id))
                        if row.fetchone() is None:
                            await interaction.followup.send("You have not rated this movie yet; please provide a score to add a new rating.")
                            return
                    if phrase == "":
                        if score:
                            cursor.execute("""UPDATE scores SET score = ? WHERE movie_id = ? AND user_id = ?""",
                                        (score_val, movie[0], interaction.user.id))
                        else:
                            await interaction.followup.send("Please provide a score or phrase to update.")
                            return
                    elif phrase == "None":
                        if score:
                            cursor.execute("""UPDATE scores SET score = ?, phrase = "" WHERE movie_id = ? AND user_id = ?""",
                                        (score_val, movie[0], interaction.user.id))
                        else:
                            cursor.execute("""UPDATE scores SET phrase = "" WHERE movie_id = ? AND user_id = ?""",
                                        (movie[0], interaction.user.id))
                    else:
                        if score:
                            cursor.execute("""UPDATE scores SET score = ?, phrase = ? WHERE movie_id = ? AND user_id = ?""",
                                        (score_val, phrase, movie[0], interaction.user.id))
                        else:
                            cursor.execute("""UPDATE scores SET phrase = ? WHERE movie_id = ? AND user_id = ?""",
                                        (phrase, movie[0], interaction.user.id))
                database.commit()
                await interaction.followup.send(f"Movie {movie[1]} ({movie[2]}) rated successfully.")
            else:
                await interaction.followup.send(f"Movie {movie[1]} ({movie[2]}) found, not rated yet.\nMultiple movies matched your search criteria; please use more specific parameters next time.")
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")
            return None



    @nextcord.slash_command(name="all")
    async def all(self,
                interaction: nextcord.Interaction,
                order: str = nextcord.SlashOption(description="Order by id, title, year, final score, or score", required=False,
                                                    choices={"ID":"id ASC",
                                                            "Title":"title ASC",
                                                            "Year":"year DESC",
                                                            "Final Score":"final_score DESC",
                                                            "Score":"score"}, default="id ASC")):
        await interaction.response.defer(ephemeral=False)
        try:
            if order == "score":
                cursor.execute("""
                    SELECT m.id, m.title, m.year, m.final_score, s.score
                    FROM movies m
                    LEFT JOIN scores s
                        ON m.id = s.movie_id AND s.user_id = ?
                    GROUP BY m.id, m.title, m.year, m.final_score
                    ORDER BY (s.score IS NULL), s.score DESC, m.final_score DESC
                """, (interaction.user.id,))
                ratings = cursor.fetchall()
                if not ratings:
                    await interaction.followup.send("There are no movies in the database.")
                    return
                pages = build_list_pages_for_movies_with_user_score_fields(
                    ratings,
                    title="All Movies",
                    color=nextcord.Color.from_rgb(0, 0, 0)
                )
            else:
                cursor.execute(f"""
                    SELECT id, title, year, final_score
                    FROM movies
                    ORDER BY {order}
                """)
                ratings = cursor.fetchall()
                if not ratings:
                    await interaction.followup.send("There are no movies in the database.")
                    return
                pages = build_list_pages_for_movies_fields(
                    [(r[0], r[1], r[2], r[3]) for r in ratings],
                    title="All Movies",
                    color=nextcord.Color.from_rgb(0, 0, 0)
                )
            view = PagedEmbeds(pages, author_id=interaction.user.id)
            await interaction.followup.send(embed=pages[0], view=view)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")
            return None



    @nextcord.slash_command(name="myrated")
    async def myrated(self,
                    interaction: nextcord.Interaction,
                    order: str = nextcord.SlashOption(description="Order by id, title, year, score, final score", required=False,
                                                    choices={"ID":"m.id ASC",
                                                            "Title":"m.title ASC",
                                                            "Year":"m.year DESC",
                                                            "Score":"s.score DESC",
                                                            "Final Score":"m.final_score DESC",}, default="m.id ASC")):
        await interaction.response.defer(ephemeral=False)
        try:
            cursor.execute(f"""SELECT m.id, m.title, m.year, m.final_score, s.score, s.phrase, n.name
                            FROM movies m
                            LEFT JOIN scores s ON m.id = s.movie_id
                            LEFT JOIN names n ON s.user_id = n.user_id
                            WHERE s.user_id = ?
                            ORDER BY {order}""", (interaction.user.id,))
            rows = cursor.fetchall()
            if not rows:
                await interaction.followup.send("You have not rated any movies.")
                return
            display_name = rows[0][6] or interaction.user.display_name or interaction.user.name
            if order == "m.final_score DESC":
                pages = build_list_pages_for_rated_fields_fs(
                    rows,
                    header_title=f"{display_name}'s Rated Movies",
                    include_phrase=True,
                    color=nextcord.Color.from_rgb(0,0,0)
                )
            else:
                pages = build_list_pages_for_rated_fields_def(
                    rows,
                    header_title=f"{display_name}'s Rated Movies",
                    include_phrase=True,
                    color=nextcord.Color.from_rgb(0,0,0)
                )
            view = PagedEmbeds(pages, author_id=interaction.user.id)
            await interaction.followup.send(embed=pages[0], view=view)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")
            return None



    @nextcord.slash_command(name="norated")
    async def norated(self,
        interaction: nextcord.Interaction,
        order: str = nextcord.SlashOption(
            description="Order by id, title, year, or final score",
            required=False,
            choices={
                "ID": "m.id ASC",
                "Title": "m.title ASC",
                "Year": "m.year DESC",
                "Final Score": "m.final_score DESC",
            },
            default="m.id ASC")):
        await interaction.response.defer(ephemeral=False)
        try:
            order_sql_map = {
                "m.id ASC": "m.id ASC",
                "m.title ASC": "m.title ASC",
                "m.year DESC": "m.year DESC",
                "m.final_score DESC": "m.final_score DESC",
            }
            order_clause = order_sql_map.get(order, "m.id ASC")
            cursor.execute(f"""
                SELECT m.id, m.title, m.year, m.final_score
                FROM movies m
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM scores s
                    WHERE s.movie_id = m.id
                    AND s.user_id  = ?
                )
                ORDER BY {order_clause}
            """, (interaction.user.id,))
            rows = cursor.fetchall()
            if not rows:
                await interaction.followup.send("You’ve already rated all movies. 🎉")
                return
            cursor.execute("SELECT name FROM names WHERE user_id = ?", (interaction.user.id,))
            row = cursor.fetchone()
            display_name = (row[0] if row and row[0] else
                            getattr(interaction.user, "global_name", None) or
                            interaction.user.display_name or
                            interaction.user.name)
            pages = build_list_pages_for_movies_fields(
                rows,
                title=f"{display_name}'s Not Rated Yet Movies",
                color=nextcord.Color.from_rgb(0, 0, 0)
            )
            view = PagedEmbeds(pages, author_id=interaction.user.id)
            await interaction.followup.send(embed=pages[0], view=view)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")
            return None



def setup(bot):
    bot.add_cog(db_ratings(bot))
