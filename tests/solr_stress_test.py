import json

h = []


def generate(string):
	if len(string) == 4:
		h.append(string)
		return
	for i in range(97, 97 + 26):
		generate(string + chr(i))


generate("")
print(len(h))
with open('../array.json', 'w', encoding='utf8') as file:
	file.write(json.dumps(h[:50000]))
