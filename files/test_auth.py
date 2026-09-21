# combien de "lignes" islice renvoie-t-il vraiment ?
body = provider.open()
first = list(itertools.islice(body, 3))
for i, x in enumerate(first):
    print(i, type(x), len(x), x[:60])   # est-ce 3 LIGNES ou 3 chunks d'octets ?
