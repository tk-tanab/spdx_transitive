class Mo:
    pList: list[str]
    aList: list[int] = []

    def __init__(self) -> None:
        self.pList=[]

    def add(self, element):
        self.aList.append(element)

    def returnPList(self):
        return self.pList

    def returnAList(self):
        return self.aList