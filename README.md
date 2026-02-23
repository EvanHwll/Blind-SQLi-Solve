# Blind SQLi Solve

Recently, I've been researching the idea of Web Exploitation and learning different methods such as SQL Injections and XSS Attacks. 
I was completing a lab on [TryHackMe](https://tryhackme.com/room/sqlilab), and reached a task which involved a Blind SQLi.

This was different to everything I had been experimenting with before, and I knew to solve this task I would have to implement some new techniques, and decided to document my approach and learning.

### Understanding the Difference

In Blind SQL Injections, you can not directly see any of the results from your injected queries. This means that you have to use alternative methods to infer them, and there are two main types: Boolean-based and Time-based.

In boolean-based, you are able to infer whether your condition evaluated to true or false based on a consistent difference in the response, such as a significantly different response length. However, time-based approaches include a wait clause in the select statement, meaning if the condition evaluates to true it delays the response by a certain amount of time.

Now that I understood the difference, I was able to approach the problem more confidently.

### Getting Started

When I opened the website, I was greeted with a simple login form. I wanted to test this form was vulnerable to SQL Injections, so I used a tautology based payload to ensure the WHERE clause always evaluated to true. I placed this inside of the username field and entered a random string as the password: the password did not matter as it was being commented out by the `--` in the payload. When submitting this form, I was able to login to an account.

```
Username: ' OR 1=1--
Password: letmein
```
After seeing that this login form was vulnerable to SQL Injection, I decided to test the responses it gave to try and find any consistent differences which would allow me to use a Boolean-Based approach. I opened BurpSuite and intercepted 2 responses from the web server: one where the login succeeded, and the other where the login failed.

<img width="500" height="550" alt="image" src="https://github.com/user-attachments/assets/12d476e2-b5e6-4e5e-adcb-55f52566e8bb" />
<img width="500" height="550" alt="image" src="https://github.com/user-attachments/assets/3bbd79bd-9631-46cc-88cc-4126de8ef9bc" />

Looking at these, there was a very significant difference between the two. Successful logins returned a **redirect** (Status Code 302), whereas a failed login returned a **HTTP OK** (Status Code 200). I tested a few more cases for each, and it remained consistent, so I would be able to use these as my check to determine if my payload evaluated to true or false.

The next logical step was to determine what database was being used so I could tailor my payloads and syntax appropriately. I knew of some payloads I could use that only evaluate to true for specific database types:
```
' OR ( SELECT COUNT(*) FROM information_schema.tables ) > 0 -- | MySQL / PostgreSQL
' OR ( SELECT COUNT(*) FROM sqlite_master ) > 0 --             | SQLite
```
After using each of these payloads in the username field, I received a 302 Response for the one for SQLite, indicating the database was built on SQLite. This was very useful to know as I could now use some built-in methods to pull information out of the database.

### Finding Table Names

Now I had all the information I needed, I could begin writing a Python program that could aid me in solving this problem. I created a new Python project and wrote a simple function that creates a POST Request to a destination with some parameters, and returns True if the response code was 302, False if it was 200, and raises a ValueError otherwise.

<img width="1344" height="534" alt="image" src="https://github.com/user-attachments/assets/bb89121c-a1a4-4a9e-9dc9-c9ceb38d4998" />

To test this was working, I created some obvious test cases that should evaluate to True and False. However, I did not get the expected results. Even though `a` should evaluate to True, it was still returning False.
<img width="1328" height="382" alt="image" src="https://github.com/user-attachments/assets/4648b77c-c000-4e21-bd6c-b5aed3e376e6" />


After reading a [discussion on StackOverflow](https://stackoverflow.com/questions/58163496/getting-200-in-response-instead-of-302), I found the reason. The requests module automatically follows redirects, meaning the response it was giving was actually for the home page of the website. To fix this, I added an extra parameter, `allow_redirects=False`. This solved the problem.

<img width="1344" height="534" alt="image" src="https://github.com/user-attachments/assets/d5c81da3-95c9-4a4f-88b6-74c8b5a6237e" />

<img width="1328" height="382" alt="image" src="https://github.com/user-attachments/assets/09f0e98c-2889-4700-abbd-cddabbc3b097" />

Now that I had this working, I could begin gathering information about the database structure to hopefully locate where the admin's password might be. The first logical step was to try and gather the table names.

First, I needed to know how many tables were in the database.

To do this, I could use the SQL Query
```
SELECT COUNT(*) FROM sqlite_master WHERE type='table'
```

But, as this was a blind injection, I would have no way to tell what this returned. Hence, I would need to ask questions about the value, such as is it equal to X, greater than Y, etc.

My first idea would be iterate through a list of numbers, and ask the database
_"Is the number of tables in your database equal to X?"_
Which would be implemented as
```
' OR ( SELECT COUNT(*) FROM sqlite_master WHERE type='table' ) = X--
```
And if this returned a 302 Redirect, it would be true and would mean that there are X tables in the database. Here is how I implemented that:
<img width="2468" height="496" alt="image" src="https://github.com/user-attachments/assets/5452d3ae-0b36-4efd-a534-99640d31721d" />

I then wrote some code to call that function and store the result in `number_of_tables`. Printing out this value gave me `1`, meaning there is only 1 table in the database.
<img width="712" height="230" alt="image" src="https://github.com/user-attachments/assets/1b1e2f09-5c68-4bcb-aa2f-3df9c6f7e0b7" />

The next thing I needed to do was figure out the name of this table so I could query it. Like before, my mind instantly went to:
```
SELECT name FROM sqlite_master WHERE type='table'
```

But again, we wouldn't be able to see the result from this. I needed to figure out a way I could ask questions about this string to the database, but this was conceptually harder, because it was unfeasible to ask it questions like "Is it 'main'?", because I'd have to loop through every word in a dictionary which it may still not even match with.

One solution I considered was iterating through every character, similarly to what I did with the numbers, and comparing each character one by one.
For example, I would ask 
_"Is the first character A?"_
**Yes** -> _"Is the second character A?"_
**No** -> _"Is the first character B?"_
and repeat until the end of the string.

But, this introduced a new problem. I would need to know where the end of the string was. To do this, I decided to use the same function I had written earlier to perform a linear search for the length of the table name.

<img width="2992" height="496" alt="image" src="https://github.com/user-attachments/assets/65853ab0-75c5-40a0-a553-04cb7d5b23c2" />

Although not required, I gave this function a parameter `tableIndex` that would allow me to specify what table number to check. In this case, I am checking the first (and only) table, so I passed in the argument `1`, and got the output `5`.

<img width="2992" height="648" alt="image" src="https://github.com/user-attachments/assets/23e27c7f-06df-449a-91ea-a7e9816afcdf" />

This meant the name of the table had 5 characters, that I could then search for.

However, I noticed one optimisation problem with my initial approach. As ASCII is stored in 7 bits, there are 128 possible characters. Making up to 128 requests per character would be inefficient and could lead to ratelimits or other limitations.

Looking at the ASCII chart, I considered changing my bounds to 32 (space) and 126 (~). However, this only reduced the range to 94 characters, which is still a very significant potential amount to make for each character.

I decided a good approach would be to implement a Binary Search, which would lower the time complexity from O(n) to O(logn). Binary search requires numerical values that can be compared, but I was using characters. However, I realised I could just use the ASCII numerical values for each character instead, meaning I could use those instead and then convert back to their character representation afterwards.

To implement this, I would use the SQLite `SUBSTR(string, startIndex, length)` method to isolate each character one by one:
```
SELECT SUBSTR(name, i, 1) FROM sqlite_master WHERE type='table'
```

I could then use the SQLite `CHAR(int)` method to convert my numerical value to its associated ASCII character:
```
CHAR(int)
```

And finally, I could compare these to determine if the numerical value is too big, too small or is a match:
```
'OR ( SELECT SUBSTR(name, 1, i) FROM sqlite_master WHERE type='table' ) > CHAR(int)--
'OR ( SELECT SUBSTR(name, 1, i) FROM sqlite_master WHERE type='table' ) < CHAR(int)--
'OR ( SELECT SUBSTR(name, 1, i) FROM sqlite_master WHERE type='table' ) = CHAR(int)--
```

Which I could then use to form the Binary Search.

Using the standard method for Binary Search, I created this function:
<img width="3454" height="1256" alt="image" src="https://github.com/user-attachments/assets/f4d9c012-989e-470c-92f0-d3430e9bca26" />

To test this worked, I used the following line:

<img width="726" height="154" alt="image" src="https://github.com/user-attachments/assets/c40d7bdb-dde7-4083-b8d5-d6346804b756" />

Meaning the first character was `u`.

I then wrote a function that combined all previous functions:
<ol>
  <li>Finds the amount of tables</li>
  <li>For each table, finds the length of the name</li>
  <li>For each name, find the amount of characters</li>
  <li>For each character, binary search its value.</li>
</ol>

<img width="1436" height="800" alt="image" src="https://github.com/user-attachments/assets/cbaf5f0c-6dad-4a02-b757-0a7e67080e27" />

Now, when I print the value of this function:

<img width="558" height="154" alt="image" src="https://github.com/user-attachments/assets/151a9a54-a98a-4c2f-a0b8-cc7d7d479552" />

Meaning the name of our table is `users`!


### Finding Field Names

Now that I had a list of table names (albeit, just the one), I can run one simple query to determine the CREATE command, which also includes the name of all fields and their data types.

```
SELECT sql FROM sqlite_master WHERE name='users'
```

However, like before, I could not see what this outputted. Luckily, I already had a solution written - the character binary search algorithm. With a few minor tweaks, I could adapt this function to now pull the characters from this result.

<img width="3114" height="1370" alt="image" src="https://github.com/user-attachments/assets/2b3e6bd8-e0b8-4c72-abd3-650a22d4915f" />

To confirm this was working, I ran the function on the first character. I should see `C`, as that is the first letter of CREATE.

<img width="880" height="154" alt="image" src="https://github.com/user-attachments/assets/d8ac566d-b94b-472a-8a4c-319f5aea021a" />

Thankfully, I saw `C`, meaning my function was working as expected.

I could then write one more function, `findCreateCommand(table_name)`, which goes through each character of the create command, figures out the character and adds it to the string.

One problem I had however, is deciding how to decide where the end of the command was. I considered reusing my code finding the length of table names to find the length of this command instead. However, a cleaner solution would be just to terminate the process when we find the character `)`, which indicates the end of the CREATE statement.

<img width="1112" height="686" alt="image" src="https://github.com/user-attachments/assets/b468c59d-51c4-4dcd-9073-a437171bfd14" />

Calling this function gives:

<img width="712" height="306" alt="image" src="https://github.com/user-attachments/assets/819d915c-8f1b-447b-9197-74a304ba7fcc" />

Meaning the field names are `id` (primary key), `username` and `password`.

### Extracting The Password

Going back to the task, the task was to extract the admin's password. This meant I could use the SQL Query

```
SELECT password FROM users WHERE username="admin"
```

To finish the task (assuming field names do as they seem). As obvious by now, I would not be able to see this, so I needed to use my binary search algorithm once more to find the password.

In order to find all the characters, I needed to find either a stopping condition or the length of the password. However, I wanted to explore one alternative method, and that was making use of the way `SUBSTR()` works.
As mentioned earlier, `SUBSTR()` has 3 parameters: `string`, `start`, `length`. However, if start is greater than the length of the actual string, the `SUBSTR()` method just returns an empty string `''`. When comparing the empty string to an ASCII value, it will **always** be less than it, meaning we will never return a character. As there are 128 characters, Binary Search will always find a value within 7 passes. This means if we reach our 8th pass without returning a character, we can assume it is the end of the string.

<img width="3128" height="1598" alt="image" src="https://github.com/user-attachments/assets/80925fc2-d71b-4d44-a5bd-e59c0aebe95b" />

<img width="1034" height="648" alt="image" src="https://github.com/user-attachments/assets/0b2443b4-8b4e-4b37-ba14-fa01dc62d6ff" />

Upon calling `findPassword("users")`, this is printed:

<img width="804" height="154" alt="image" src="https://github.com/user-attachments/assets/803601b8-ace1-4707-95e2-f0a2eb760597" />

**Which is our flag to solve the puzzle!**




















