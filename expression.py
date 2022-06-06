from pHelpers import removeEmptyElements

# CLASS expression 
# eType: stores the type of the relationship (and, or, boolean)
# subExpressions: stores an array of expressions, either of type expression or str
# __init__(eType, subExpressions): the constructor. deals with None values and converting to boolean if neccessary 
# getFullExpression(): returns the whole expression as a string 
# getPrereqs(): returns prereqs as a 1D array of strings 
# fixBrackets(): removes unneccessary chains of boolean objects. modifies its object, no return 
# evaluateExpression(): TODO determines whether the requirement for the class have been met 
class Expression: 
    def __init__(self, eType, subExpressions):
        
        # Goes through all subExpressions and removes any where the Type is none 
        # Iterating backwards prevents the index from "skipping" when an element is removed 
        for i in range(len(subExpressions) - 1, -1, -1):
            if type(subExpressions[i]) is Expression and subExpressions[i].eType == None:
                del subExpressions[i]

        # Removes any blank elements in the array, and returns None if all are removed
        subExpsP = removeEmptyElements(subExpressions)

        # Will only happen if the array is all None values
        # Expressions of eType == None are removed by parent expression objects, however if this expression is the root, then, 
        # Expressions of subExpressisons == None are returned as None in getFullExpression()
        if subExpsP == None:
            self.eType = None
            self.subExpressions = None
            return 
        
        # Prevents having an eType of and/or with one value 
        # Example: expression("or", exp1, exp2) where exp2 is None is changed to eType boolean and exp2 is removed 
        if len(subExpsP) <= 1:
            self.eType = "boolean"
        else:
            self.eType = eType
        
        self.subExpressions = subExpsP

    def getFullExpression(self):
        #print(f"{self.eType} {self.subExpressions}")
        # This should only happen if the root expression is None, since otherwise the constructor will handle it 
        if self.subExpressions == None:
            return "None"
        
        # expressions of eType boolean are of type string, unless the type was changed in the constructor 
        if self.eType == "boolean" and type(self.subExpressions[0]) is str:
            return f"{self.subExpressions[0]}"
        
        # If eType is boolean, it's redunant to have it in the string since it will be obvious 
        if self.eType != "boolean":
            expression = f"{self.eType}"
        else: 
            expression = ""
         
        for subExpression in self.subExpressions:
            expression += f"[{subExpression.getFullExpression()}]"
        return expression

    # TODO: Test this 
    def getPrereqs(self):
        prereqs = []
        if self.subExpressions == None:
            return prereqs
        
        if self.eType == "boolean":
            prereqs.extend(self.subExpressions)
        else:
            for expression in self.subExpressions:
                prereqs.extend(expression.getPrereqs())

        return prereqs
    
    def fixBrackets(self):
        if self.subExpressions == None:
            return
        if self.eType == "boolean":
            if type(self.subExpressions[0]) is Expression and self.subExpressions[0].eType == "boolean":
                self.subExpressions = self.subExpressions[0].subExpressions
                self.fixBrackets()
            elif type(self.subExpressions[0]) is Expression and (self.subExpressions[0].eType == "and" or self.subExpressions[0].eType == "or"):
                self.eType = self.subExpressions[0].eType
                self.subExpressions = self.subExpressions[0].subExpressions
                self.fixBrackets()
        elif self.eType == "or":
            # first check if all the sub exps are or 
            matching = True
            for subExp in self.subExpressions:
                if subExp.eType == "and":
                    matching = False
            # merge if matching
            if matching == True:
                newSubExp = []
                for subExp in self.subExpressions:
                    if subExp.eType == 'or':
                        newSubExp.extend(subExp.subExpressions)
                    else:
                        newSubExp.append(subExp)
                if self.subExpressions != newSubExp:
                    self.subExpressions = newSubExp
                    self.fixBrackets()
        elif self.eType == "and":
            newSubExp = []
            for subExp in self.subExpressions:
                if subExp.eType == "and":
                    newSubExp.extend(subExp.subExpressions)
                else:
                    newSubExp.append(subExp)
            if self.subExpressions != newSubExp:
                self.subExpressions = newSubExp
                self.fixBrackets()

        for subExp in self.subExpressions:
            if type(subExp) is Expression:
                subExp.fixBrackets()

    # TODO: requires a list of completed courses  
    def evaluateExpression(self):
        if self.eType == "or":
            return None
        elif self.eType == "and":
            return None
        elif self.eType == "boolean":
            return None