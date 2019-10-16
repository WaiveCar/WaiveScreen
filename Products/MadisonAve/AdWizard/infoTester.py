import json
def infoTester(infoFile):
    fAns = open("test/answers.json")
    jsonAns = json.loads(fAns.read())
    fAns.close()
    fInfo = open(infoFile)
    jsonInfo = json.loads(fInfo.read())
    fInfo.close()
    for x in jsonAns:
        if (x == jsonInfo["website"]):
            print("Results accquired from \"" + jsonInfo["website"] + "\":")
            for y in jsonAns[x]:
                if y in jsonInfo:
                    if(jsonAns[x][y] == jsonInfo[y]):
                        print(y+": success")
                    else:
                        print(y+": unsuccessful")
                else:
                    print(y+": key not present")
            break

infoTester("siteInfo/info.json")
