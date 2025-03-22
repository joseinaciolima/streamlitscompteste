import pulp

# Definir o problema de otimização
problem = pulp.LpProblem("Maximizar_Receita", pulp.LpMaximize)

# Variáveis de decisão
x1 = pulp.LpVariable("Country", lowBound=0, cat='Continuous')  # quantidade de mesas Country
x2 = pulp.LpVariable("Moderna", lowBound=0, cat='Continuous')  # quantidade de mesas Moderna

# Função objetivo: Maximizar a receita
problem += 1350 * x1 + 1550 * x2, "Receita"

# Restrições de disponibilidade semanal das máquinas
problem += 1.5 * x1 + 2 * x2 <= 1000, "Disponibilidade_Serra"
problem += 3 * x1 + 4.5 * x2 <= 2000, "Disponibilidade_Lixad"
problem += 2.5 * x1 + 1.5 * x2 <= 1500, "Disponibilidade_Polim"

# Restrições de proporção mínima de produção
problem += x1 >= 0.2 * (x1 + x2), "Minimo_Country"
problem += x2 >= 0.3 * (x1 + x2), "Minimo_Moderna"

# Resolver o problema
problem.solve()

# Coletar os resultados
solution = {
    "Quantidade de mesas Country": x1.varValue,
    "Quantidade de mesas Moderna": x2.varValue,
    "Receita total": pulp.value(problem.objective)
}

print(solution)
