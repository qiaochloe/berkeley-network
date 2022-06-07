# Processes arrays for removing prereqs
def removeEmptyElements(array):
    # Removes empty strings from an array 
    #print(f"in {array}")
    out = [i for i in array if i]
    if len(out) == 0:
        out = None
    #print(f"out {out}")
    return out