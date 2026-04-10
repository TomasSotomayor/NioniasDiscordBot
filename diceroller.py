import random
import re

import nextcord
from nextcord.ext import commands



class db_diceroller(commands.Cog):
    def __init__(self, bot):
        self.bot = bot



    @nextcord.slash_command(name="roll")
    async def roll(self,
                   interaction: nextcord.Interaction,
                   roll: str = nextcord.SlashOption(description="Dices rolled", required=True),
                   typed: str = nextcord.SlashOption(description="Type of Dice: Normal, Star Wars, or Custom (Star Wars with numbers)", required=False,
                                                    choices={"Normal":"normal",
                                                            "Star Wars":"sw",
                                                            "Custom":"custom"}, default="normal")):
        await interaction.response.defer(ephemeral=False)



        if typed == "normal":
            try:
                validez = "Ingrese una petición válida."
                cantidades = []
                lados = []
                bonos = []
                penas = []
                resultados = []
                if(roll == "" or roll.isdigit()):
                    await interaction.followup.send(validez)
                    return
                lista = []
                for i in range(len(roll)):
                    lista.append(roll[i])
                while(True):
                    for i in range(len(lista)):
                        if(i != 0):
                            if(lista[i] == "d" and not str(lista[i-1]).isdigit()):
                                lista.insert(i,"1")
                                break
                    if(i < len(lista)-1):
                        if(lista[i+1] == "d" and str(lista[i]).isdigit()):
                            continue
                    break
                if("d" not in lista or i in ["d","+","-"]):
                    await interaction.followup.send(validez)
                    return
                n_roll = ""
                for i in range(len(lista)):
                    n_roll = f"{n_roll}{lista[i]}"
                if(lista[i] in ["d","+","-"]):
                    await interaction.followup.send(validez)
                    return
                numeros = re.split(r'[d+\- ]', n_roll)
                while(True):
                    for i in range(len(numeros)):
                        if(numeros[i] in ""):
                            break
                        elif not numeros[i].isdigit():
                            await interaction.followup.send(validez)
                            break
                    if(numeros[i] == ""):
                        numeros.pop(i)
                        continue
                    elif not numeros[i].isdigit():
                        break
                    break
                if not numeros[i].isdigit():
                    return
                secciones = re.split(r'[1234567890 ]', n_roll)
                while(True):
                    for i in range(len(secciones)):
                        if(secciones[i] == ""):
                            break
                        elif(secciones[i] not in ["d","+","-"]):
                            await interaction.followup.send(validez)
                            break
                    if(secciones[i] == ""):
                        secciones.pop(i)
                        continue
                    elif(secciones[i] not in ["d","+","-"]):
                        break
                    break
                if(secciones[i] not in ["d","+","-"]):
                    return
                elif(n_roll[0] in ["+","-"]):
                    await interaction.followup.send(validez)
                    return
                elif(secciones.count("d")-1 > secciones.count("+") + secciones.count("-")):
                    await interaction.followup.send(validez)
                    return
                elif(n_roll[0] == "d"):
                    numeros.insert(0, 1)
                tiradas = ""
                texto = f"{roll}"
                contador = 0
                for i in range(len(secciones)):
                    if(secciones[i] == "d"):
                        if(i == 0):
                            cantidades.append(numeros[i])
                            if(numeros[i+1] == "0"):
                                break
                            lados.append(numeros[i+1])
                            tiradas = f"{tiradas}; ({cantidades[len(cantidades)-1]}d{lados[len(lados)-1]})"
                            texto = f"{texto}; ({cantidades[len(cantidades)-1]}d{lados[len(lados)-1]})"
                            for j in range(0, int(cantidades[i])):
                                resultados.append(random.randint(1, int(lados[i])))
                                tiradas = f"{tiradas}, {resultados[contador]}"
                                texto = f"{texto}, {resultados[contador]}"
                                contador += 1
                        else:
                            if(secciones[i-1] == "+"):
                                if(numeros[i+1] == "0"):
                                    break
                                cantidades.append(numeros[i])
                                lados.append(numeros[i+1])
                                tiradas = f"{tiradas}; ({cantidades[len(cantidades)-1]}d{lados[len(lados)-1]})"
                                texto = f"{texto}; ({cantidades[len(cantidades)-1]}d{lados[len(lados)-1]})"
                                for j in range(0, int(cantidades[len(cantidades)-1])):
                                    resultados.append(random.randint(1, int(lados[len(lados)-1])))
                                    tiradas = f"{tiradas}, {resultados[contador]}"
                                    texto = f"{texto}, {resultados[contador]}"
                                    contador += 1
                            elif(secciones[i-1] == "-"):
                                if(numeros[i+1] == "0"):
                                    break
                                cantidades.append(numeros[i])
                                lados.append(numeros[i+1])
                                tiradas = f"{tiradas}; ({cantidades[len(cantidades)-1]}d{lados[len(lados)-1]})"
                                texto = f"{texto}; ({cantidades[len(cantidades)-1]}d{lados[len(lados)-1]})"
                                for j in range(0, int(cantidades[len(cantidades)-1])):
                                    resultados.append(random.randint(1, int(lados[len(lados)-1])))
                                    tiradas = f"{tiradas}, {resultados[contador]}"
                                    texto = f"{texto}, {resultados[contador]}"
                                    resultados[contador] = -resultados[contador]
                                    contador += 1
                    elif(secciones[i] == "+"):
                        if(i+1 < len(secciones)):
                            if(secciones[i+1] != "d"):
                                bonos.append(int(numeros[i+1]))
                        elif(i+1 == len(secciones)):
                            bonos.append(int(numeros[i+1]))
                    elif(secciones[i] == "-"):
                        if(i+1 < len(secciones)):
                            if(secciones[i+1] != "d"):
                                penas.append(int(numeros[i+1]))
                        elif(i+1 == len(secciones)):
                            penas.append(int(numeros[i+1]))
                if(numeros[i+1] == "0"):
                    await interaction.followup.send(validez)
                    return
                tiradas = tiradas[2:]
                if(len(bonos) == 0 and len(penas) == 0):
                    total = sum(resultados)
                elif(len(bonos) > 0 and len(penas) == 0):
                    total = sum(resultados)+sum(bonos)
                elif(len(bonos) == 0 and len(penas) > 0):
                    total = sum(resultados)-sum(penas)
                else:
                    total = sum(resultados)+sum(bonos)-sum(penas)
                embed = nextcord.Embed(
                title=roll,
                description=f"""- Resultados: {tiradas}.
- Total: {total}.""",
                color=nextcord.Color.from_rgb(0, 0, 0))
                await interaction.followup.send(embed=embed)
            except Exception as e:
                await interaction.followup.send(f"An error occurred: {e}")



        elif typed == "sw":
            cant = []
            letr = []
            resu = []
            if "a" not in roll.lower() and "b" not in roll.lower() and "c" not in roll.lower() and "d" not in roll.lower() and "p" not in roll.lower() and "s" not in roll.lower() and "f" not in roll.lower() and "1" not in roll and "2" not in roll and "3" not in roll and "4" not in roll and "5" not in roll and "6" not in roll and "7" not in roll and "8" not in roll and "9" not in roll:
                return
            elif roll.isdigit() or len(roll) <= 1 or roll[len(roll)-1].isdigit() or roll[0].isalpha():
                return
            for i in range(len(roll)):
                if roll[i] not in ["a", "b", "c", "d", "p", "s", "f", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
                    break
                if i+1 < len(roll):
                    if roll[i].isdigit() and roll[i+1].isdigit() or roll[i].isalpha() and roll[i+1].isalpha():
                        break
                if roll[i].isdigit():
                    cant.append(int(roll[i]))
                else:
                    letr.append(roll[i].lower())
            for j in range(len(cant)):
                if letr[j] == "b" or letr[j] == "s":
                    xd = 6
                elif letr[j] == "a" or letr[j] == "d":
                    xd = 8
                else:
                    xd = 12
                for k in range(1, cant[j]):
                    result = random.randint(1, xd)
                    if letr[j] == "b":
                        if result == 3:
                            resu.append("Success")
                        elif result == 4:
                            resu.append("Success")
                            resu.append("Advantage")
                        elif result == 5:
                            resu.append("Advantage")
                            resu.append("Advantage")
                        elif result == 6:
                            resu.append("Advantage")
                    elif letr[j] == "a":
                        if result in [2, 3]:
                            resu.append("Success")
                        elif result == 4:
                            resu.append("Success")
                            resu.append("Success")
                        elif result in [5, 6]:
                            resu.append("Advantage")
                        elif result == 7:
                            resu.append("Success")
                            resu.append("Advantage")
                        elif result == 8:
                            resu.append("Advantage")
                            resu.append("Advantage")
                    elif letr[j] == "p":
                        if result in [2, 3]:
                            resu.append("Success")
                        elif result in [4, 5]:
                            resu.append("Success")
                            resu.append("Success")
                        elif result in [6]:
                            resu.append("Advantage")
                        elif result in [7, 8, 9]:
                            resu.append("Success")
                            resu.append("Advantage")
                        elif result in [10, 11]:
                            resu.append("Advantage")
                            resu.append("Advantage")
                        elif result == 12:
                            resu.append("Triumph")
                    elif letr[j] == "s":
                        if result in [3, 4]:
                            resu.append("Failure")
                        elif result in [5, 6]:
                            resu.append("Threat")
                    elif letr[j] == "d":
                        if result == 2:
                            resu.append("Failure")
                        elif result == 3:
                            resu.append("Failure")
                            resu.append("Failure")
                        elif result in [4, 5, 6]:
                            resu.append("Threat")
                        elif result == 7:
                            resu.append("Threat")
                            resu.append("Threat")
                        elif result == 8:
                            resu.append("Failure")
                            resu.append("Threat")
                    elif letr[j] == "c":
                        if result in [2, 3]:
                            resu.append("Failure")
                        elif result in [4, 5]:
                            resu.append("Failure")
                            resu.append("Failure")
                        elif result in [6, 7]:
                            resu.append("Threat")
                        elif result in [8, 9]:
                            resu.append("Threat")
                            resu.append("Failure")
                        elif result in [10, 11]:
                            resu.append("Threat")
                            resu.append("Threat")
                        elif result == 12:
                            resu.append("Despair")
                    else:
                        if result in [1, 2, 3, 4, 5, 6]:
                            resu.append("Dark Side")
                        elif result == 7:
                            resu.append("Dark Side")
                            resu.append("Dark Side")
                        elif result in [8, 9]:
                            resu.append("Light Side")
                        else:
                            resu.append("Light Side")
                            resu.append("Light Side")
            if i+1 < len(roll):
                if roll[i] not in ["a", "b", "c", "d", "p", "s", "f", "1", "2", "3", "4", "5", "6", "7", "8", "9"] or roll[i].isdigit() and roll[i+1].isdigit() or roll[i].isalpha() and roll[i+1].isalpha():
                    return
            numa = resu.count("Success") + resu.count("Triumph") - resu.count("Failure") - resu.count("Despair")
            numb = resu.count("Advantage") - resu.count("Threat")
            numc = resu.count("Triumph") - resu.count("Despair")
            if numa >= 1:
                conc = f"¡Éxito ({numa})"
                if numb >= 1:
                    conc += f" con Ventaja ({numb})"
                    if numc >= 1:
                        conc += f" y Triunfo ({numc})"
                    elif numc < 0:
                        conc += f" y Desesperación ({numc * -1})"
                    conc += "!"
                elif numb < 0:
                    conc += f" con Amenaza ({numb * -1})"
                    if numc >= 1:
                        conc += f" y Triunfo ({numc})"
                    elif numc < 0:
                        conc += f" y Desesperación ({numc * -1})"
                    conc += "!"
                else:
                    if numc >= 1:
                        conc += f" con Triunfo ({numc})"
                    elif numc < 0:
                        conc += f" con Desesperación ({numc * -1})"
                    conc += "!"
                color = 0x00ff00
            else:
                conc = f"¡Fracaso ({numa * -1})"
                if numb >= 1:
                    conc += f" con Ventaja ({numb})"
                    if numc >= 1:
                        conc += f" y Triunfo ({numc})"
                    elif numc < 0:
                        conc += f" y Desesperación ({numc * -1})"
                    conc += "!"
                elif numb < 0:
                    conc += f" con Amenaza ({numb * -1})"
                    if numc >= 1:
                        conc += f" y Triunfo ({numc})"
                    elif numc < 0:
                        conc += f" y Desesperación ({numc * -1})"
                    conc += "!"
                else:
                    if numc >= 1:
                        conc += f" con Triunfo ({numc})"
                    elif numc < 0:
                        conc += f" con Desesperación ({numc * -1})"
                    conc += "!"
                color = 0xff0000
            desc = f"""- Tirada: {roll}.
- Resultados: """
            if "Triumph" in resu:
                desc += f"{resu.count('Triumph')} Triunfo(s), "
            if "Despair" in resu:
                desc += f"{resu.count('Despair')} Desesperación(es), "
            if "Advantage" in resu:
                desc += f"{resu.count('Advantage')} Ventaja(s), "
            if "Threat" in resu:
                desc += f"{resu.count('Threat')} Amenaza(s), "
            if "Success" in resu:
                desc += f"{resu.count('Success')} Éxito(s), "
            if "Failure" in resu:
                desc += f"{resu.count('Failure')} Fracaso(s), "
            if resu == []:
                desc += "Ninguno."
            else:
                desc = desc[:-2] + "."
            embed = nextcord.Embed(title=conc, description=desc, color=color)
            await interaction.followup.send(embed=embed)



        else:
            cant = []
            letr = []
            resu = []
            pos = True
            if "h" not in roll.lower() and "l" not in roll.lower() and "m" not in roll.lower() and "1" not in roll and "2" not in roll and "3" not in roll and "4" not in roll and "5" not in roll and "6" not in roll and "7" not in roll and "8" not in roll and "9" not in roll and "+" not in roll and "-" not in roll:
                return
            elif roll.isdigit() or len(roll) <= 1 or roll[len(roll)-1].isdigit() or roll[0].isalpha():
                return
            for i in range(len(roll)):
                if roll[i] not in ["h", "l", "m", "1", "2", "3", "4", "5", "6", "7", "8", "9", "+", "-"]:
                    break
                if i+1 < len(roll):
                    if roll[i].isdigit() and roll[i+1].isdigit() or roll[i].isalpha() and roll[i+1].isalpha():
                        break
                if roll[i] == "+":
                    pos = True
                    continue
                elif roll[i] == "-":
                    pos = False
                    continue
                if roll[i].isdigit():
                    if pos == True:
                        cant.append(int(roll[i]))
                    else:
                        cant.append(int(roll[i]) * -1)
                else:
                    letr.append(roll[i].lower())
            for j in range(len(cant)):
                if letr[j] == "l":
                    xd = 2
                elif letr[j] == "m":
                    xd = 4
                else:
                    xd = 6
                if cant[j] > 0:
                    for k in range(1, cant[j]+1):
                        resu.append(random.randint(1, xd)-1)
                else:
                    for k in range(1, (cant[j]*-1)+1):
                        resu.append((random.randint(1, xd)-1) * -1)
            if i+1 < len(roll):
                if roll[i] not in ["h", "l", "m", "1", "2", "3", "4", "5", "6", "7", "8", "9"] or roll[i].isdigit() and roll[i+1].isdigit() or roll[i].isalpha() and roll[i+1].isalpha():
                    return
            if sum(resu) > 0:
                conc = "¡Éxito!"
                color = 0x00ff00
            else:
                conc = "¡Fracaso!"
                color = 0xff0000
            embed = nextcord.Embed(title=conc, description=f"""Resultado Final: {sum(resu)}
Resultados: {", ".join(map(str, resu))}""", color=color)
            await interaction.followup.send(embed=embed)




def setup(bot):
    bot.add_cog(db_diceroller(bot))
