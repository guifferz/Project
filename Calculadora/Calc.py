"""Calculadora com interface gráfica (tkinter).

Aceita expressões completas e números negativos, por exemplo:
    100 - 200      ->  -100
    -5 * -3        ->  15
    (2 + 3) * -4   ->  -20
    10 / 4         ->  2.5

Operadores: + - * / ** %  e parênteses. Aceita vírgula como separador decimal.
Teclado: Enter calcula, Esc limpa, Backspace apaga.
"""

import ast
import operator
import tkinter as tk

OPERADORES_BINARIOS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}

OPERADORES_UNARIOS = {
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

LIMITE_EXPOENTE = 1000


def _avaliar(no):
    """Avalia um nó da árvore sintática aceitando só números e operadores."""
    if isinstance(no, ast.Expression):
        return _avaliar(no.body)

    if isinstance(no, ast.Constant) and isinstance(no.value, (int, float)) \
            and not isinstance(no.value, bool):
        return no.value

    if isinstance(no, ast.UnaryOp) and type(no.op) in OPERADORES_UNARIOS:
        return OPERADORES_UNARIOS[type(no.op)](_avaliar(no.operand))

    if isinstance(no, ast.BinOp) and type(no.op) in OPERADORES_BINARIOS:
        esquerda = _avaliar(no.left)
        direita = _avaliar(no.right)
        if isinstance(no.op, (ast.Div, ast.Mod)) and direita == 0:
            raise ZeroDivisionError("divisão por zero")
        if isinstance(no.op, ast.Pow) and abs(direita) > LIMITE_EXPOENTE:
            raise ValueError("expoente muito grande")
        return OPERADORES_BINARIOS[type(no.op)](esquerda, direita)

    raise ValueError("expressão inválida")


def calcular(expressao):
    """Calcula uma expressão em texto e devolve o número."""
    texto = expressao.strip().replace(",", ".").replace("×", "*").replace("÷", "/")
    if not texto:
        raise ValueError("expressão vazia")
    try:
        arvore = ast.parse(texto, mode="eval")
    except SyntaxError:
        raise ValueError("expressão inválida") from None
    return _avaliar(arvore)


def formatar(valor):
    """Mostra inteiros sem '.0' e limita as casas decimais."""
    if isinstance(valor, float):
        if valor != valor or valor in (float("inf"), float("-inf")):
            raise ValueError("resultado fora do limite")
        if valor == int(valor) and abs(valor) < 1e15:
            return str(int(valor))
        return f"{valor:.10g}".replace(".", ",")
    return str(valor)


class Calculadora(tk.Tk):
    COR_FUNDO = "#1e1e2e"
    COR_TELA = "#11111b"
    COR_TEXTO = "#cdd6f4"
    COR_NUMERO = "#313244"
    COR_OPERADOR = "#45475a"
    COR_IGUAL = "#a6e3a1"
    COR_LIMPAR = "#f38ba8"

    def __init__(self):
        super().__init__()
        self.title("Calculadora")
        self.configure(bg=self.COR_FUNDO)
        self.resizable(False, False)

        self.expressao = ""
        self.recem_calculado = False

        self._criar_tela()
        self._criar_botoes()
        self._ligar_teclado()

    # ---------- interface ----------
    def _criar_tela(self):
        self.var_historico = tk.StringVar()
        self.var_tela = tk.StringVar(value="0")

        tk.Label(
            self, textvariable=self.var_historico, anchor="e",
            bg=self.COR_TELA, fg="#7f849c", font=("Segoe UI", 11),
            padx=12, pady=6,
        ).grid(row=0, column=0, columnspan=4, sticky="ew", padx=10, pady=(10, 0))

        tk.Label(
            self, textvariable=self.var_tela, anchor="e",
            bg=self.COR_TELA, fg=self.COR_TEXTO, font=("Segoe UI", 26, "bold"),
            padx=12, pady=8,
        ).grid(row=1, column=0, columnspan=4, sticky="ew", padx=10, pady=(0, 10))

    def _criar_botoes(self):
        # (texto, ação, cor)
        linhas = [
            [("C", "limpar", self.COR_LIMPAR), ("⌫", "apagar", self.COR_OPERADOR),
             ("%", "%", self.COR_OPERADOR), ("÷", "/", self.COR_OPERADOR)],
            [("7", "7", self.COR_NUMERO), ("8", "8", self.COR_NUMERO),
             ("9", "9", self.COR_NUMERO), ("×", "*", self.COR_OPERADOR)],
            [("4", "4", self.COR_NUMERO), ("5", "5", self.COR_NUMERO),
             ("6", "6", self.COR_NUMERO), ("−", "-", self.COR_OPERADOR)],
            [("1", "1", self.COR_NUMERO), ("2", "2", self.COR_NUMERO),
             ("3", "3", self.COR_NUMERO), ("+", "+", self.COR_OPERADOR)],
            [("±", "sinal", self.COR_OPERADOR), ("0", "0", self.COR_NUMERO),
             (",", ".", self.COR_NUMERO), ("=", "igual", self.COR_IGUAL)],
            [("(", "(", self.COR_OPERADOR), (")", ")", self.COR_OPERADOR),
             ("xʸ", "**", self.COR_OPERADOR), ("", None, self.COR_FUNDO)],
        ]

        for i, linha in enumerate(linhas):
            for j, (texto, acao, cor) in enumerate(linha):
                if acao is None:
                    continue
                fg = "#11111b" if cor in (self.COR_IGUAL, self.COR_LIMPAR) else self.COR_TEXTO
                tk.Button(
                    self, text=texto, width=5, height=2,
                    font=("Segoe UI", 14), bg=cor, fg=fg,
                    activebackground="#585b70", activeforeground=self.COR_TEXTO,
                    relief="flat", bd=0,
                    command=lambda a=acao: self._acao(a),
                ).grid(row=i + 2, column=j, padx=4, pady=4)

        for coluna in range(4):
            self.grid_columnconfigure(coluna, weight=1)
        self.grid_rowconfigure(8, minsize=6)

    def _ligar_teclado(self):
        self.bind("<Return>", lambda e: self._acao("igual"))
        self.bind("<KP_Enter>", lambda e: self._acao("igual"))
        self.bind("<Escape>", lambda e: self._acao("limpar"))
        self.bind("<BackSpace>", lambda e: self._acao("apagar"))
        self.bind("<Key>", self._tecla)

    def _tecla(self, evento):
        permitidos = "0123456789+-*/%().,"
        if evento.char and evento.char in permitidos:
            self._acao("." if evento.char == "," else evento.char)

    # ---------- lógica ----------
    def _atualizar_tela(self):
        self.var_tela.set(self.expressao.replace(".", ",") if self.expressao else "0")

    def _acao(self, acao):
        if acao == "limpar":
            self.expressao = ""
            self.var_historico.set("")
            self.recem_calculado = False
        elif acao == "apagar":
            self.expressao = self.expressao[:-1]
            self.recem_calculado = False
        elif acao == "igual":
            self._calcular()
            return
        elif acao == "sinal":
            self._inverter_sinal()
        else:
            self._inserir(acao)
        self._atualizar_tela()

    def _inserir(self, simbolo):
        eh_operador = simbolo in ("+", "-", "*", "/", "%", "**")
        # Depois de um resultado, número novo recomeça; operador continua a conta.
        if self.recem_calculado and not eh_operador:
            self.expressao = ""
        self.recem_calculado = False
        self.expressao += simbolo

    def _inverter_sinal(self):
        if not self.expressao:
            self.expressao = "-"
        elif self.expressao.startswith("-(") and self.expressao.endswith(")"):
            self.expressao = self.expressao[2:-1]
        elif self.expressao.startswith("-") and not any(
                c in self.expressao[1:] for c in "+-*/%()"):
            self.expressao = self.expressao[1:]
        else:
            self.expressao = f"-({self.expressao})"
        self.recem_calculado = False

    def _calcular(self):
        if not self.expressao:
            return
        try:
            resultado = formatar(calcular(self.expressao))
        except ZeroDivisionError:
            self.var_historico.set(self.expressao.replace(".", ","))
            self.var_tela.set("Divisão por zero")
            self.expressao = ""
            return
        except (ValueError, OverflowError):
            self.var_historico.set(self.expressao.replace(".", ","))
            self.var_tela.set("Expressão inválida")
            self.expressao = ""
            return

        self.var_historico.set(f"{self.expressao.replace('.', ',')} =")
        self.expressao = resultado.replace(",", ".")
        self.recem_calculado = True
        self._atualizar_tela()


if __name__ == "__main__":
    Calculadora().mainloop()