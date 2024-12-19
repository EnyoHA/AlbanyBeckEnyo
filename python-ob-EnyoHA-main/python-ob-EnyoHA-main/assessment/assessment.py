
'''
# example of how to bind a url to a function, will be good for registration
# log in, basket and orders. Also view book? 
def userGreet():
    return 'Enyo'
app.add_url_rule('/', 'index', gfg)
'''

from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
# flask has a session package which makes this way easier
# golang forum project was comlicated by figuring out session storage
# does mean you need to set a secret key
# need to do sessions as basket doesn't work, probably the same for user editing
from flask import session
# try to see if I can do without first as request has a cookies function
import html

app = Flask(__name__)
app.secret_key = 'secret'

class Book:
    def __init__(self, title, author, isbn, price, overview):
        self.title = title
        self.author = author
        self.isbn = isbn
        self.price = price
        self.overview = overview # .decode('utf-8') if isinstance(overview, bytes) else overview

class Basket:
    def __init__(self):
        self.items = []
        
    def addBook(self, book):
        self.items.append(book)
        
    def removeBook(self, book):
        if book in self.items:
            self.items.remove(book)
        
    def viewBasket(self):
        return self.items
        
    def basketTotal(self):
        return sum(book.price for book in self.items)
    
    def fromListToDict(self):
        return {'items': [book.__dict__ for book in self.items]}
        
    # @classmethod means the methond(function) acts on the class itself
    # cls is the class(Basket)
    @classmethod
    def fromDictToList(cls, data):
        basket = cls()
        if 'items' in data and isinstance(data['items'], list):
            for bookData in data['items']:
                if isinstance(bookData, dict):
                    book = Book(**bookData)
                    basket.addBook(book)
        return basket
        
        '''
        for bookData in data.get('items', []):
            # passing the data directly to the book class
            book = Book(**bookData)
            basket.addBook(book)
        return basket'''


# split the txt file into 5 line chunks as splitting by comma caused issues with
# overviews
# could leave out overviews for display? Cause issues later with single book view?
# possible to clean so can use same function for order history?
def loadBooks(filename):
    books = []
    # need to add the encoding to account for errors when showing special characters in the overview
    with open(filename, 'r', encoding = 'utf-8') as file:
        lines = file.readlines()
        # range(<start>, <stop>, <step>)
        for i in range(0, len(lines), 5):
            title = lines[i].strip()
            author = lines[i+1].strip()
            isbn = lines[i+2].strip()
            # the pound sign used in the test file causes a special charcater to be shown
            # so i strip it and add it back in the html
            price = float(lines[i+3].strip().split('£')[1])
            overview = lines[i+4].strip()
            book = Book(title, author, isbn, price, overview)
            books.append(book)
            file.close()
    return books
        

books = loadBooks('books.txt')

'''
if 'basket' not in session:
    session['basket'] = [] # Basket()
'''

@app.route('/')
def index():
    '''
    if 'basket' not in session:
        session['basket'] = Basket()
    if 'email' in session:
        email = session['email']
        return render_template('index.html', books = books, email = email)'''
    if 'email' in session:
        email = session['email']
        user = readUsers()
        firstname = user[email]['firstname']
        return render_template('index.html', books = books, firstname = firstname)
    else:
        return render_template('index.html', books = books)
        

@app.route('/bookDeets/<isbn>')
def bookDeets(isbn):
    book = next((book for book in books if book.isbn == isbn), None)
    if book:
        return render_template('bookDeets.html', book=book)
    return 'book not found', 404
# @app.route('/register')
# def register():

@app.route('/search')
def searchBooks():
    query = request.args.get('query')
    if query:
        results = [book for book in books if query.lower() in book.title.lower()]
        return render_template('search.html', query = query, results = results)
    else:
        return render_template('search.html', query = query, results = [])

# very insecure can change if I have time
def readUsers():
    users = {}
    with open('users.txt', 'r') as file:
        for line in file:
            email, password, firstname, lastname = line.strip().split(',')
            users[email] = {'email': email, 'password': password, 'firstname': firstname, 'lastname': lastname}
            # file.close()
    return users

def writeUsers(email, password, firstname, lastname):
    with open('users.txt', 'a') as file:
        file.write(f'{email},{password},{firstname},{lastname}\n')
        # file.close()

# currently a redundant function
def checkLogIn():
    # return 'email' in request.cookies
    return 'email' in session

# this is wihtout flask log in, if time use flask log in
# need to do methods as there is two in this function rather than 1 like the others
@app.route('/login', methods=['GET', 'POST'])
def login():
    # check if post or get. if it is post it's checking for entered credentials
    # if get it is showing the log in page
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users = readUsers()
        if email in users and users[email]['password'] == password:
            session['email'] = email
            return redirect('/')
            # response = redirect('/')
            # response.set_cookie('email', value = email)
            # return response
        else:
            return render_template('/login.html', error = 'invalid email password combo')
    else:
        return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('basket', None)
    return redirect('/')
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    # check if post or get. if it is post it's checking for entered credentials
    # if get it is showing the log in page
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        password = request.form['password']
        users = readUsers()
        if email in users:
            return render_template('register.html', error = 'email already taken')
        else:
            writeUsers(email, password, firstname, lastname)
            return redirect('/login')
    else:
        return render_template('register.html')

def updateDetails(email, newPassword=None, newFirstname=None, newLastname=None):
    users = readUsers()
    if email in users:
        user = users[email]
        if newPassword:
            user['password'] = newPassword
        if newPassword:
            user['firstname'] = newFirstname
        if newPassword:
            user['lastname'] = newLastname
        users[email] = user
        with open('users.txt', 'w') as file:
            for emailID, data in users.items():
                file.write(f'{emailID},{data['password']},{data['firstname']},{data['lastname']}\n')
        return True
    return False

# turn the logic of checking the email into a function where the html and message are the parameters

@app.route('/userDeets')
def userDeets():
    # dont really need this logic as the html handles it, more secure here?
    if 'email' in session:
        email = session['email']
        users = readUsers()
        if email in users:
            user = users[email]
            return render_template('userDeets.html', user = user)
        else:
            return render_template('error.html', message = 'some kind of issue')

@app.route('/updateUserDeets', methods=['GET', 'POST'])
def updateUser():
    if request.method == 'GET':
        if 'email' in session:
            email = session['email']
            users = readUsers()
            if email in users:
                user = users[email]
                return render_template('updateUserDeets.html', user = user)
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        
        if updateDetails(email, password, firstname, lastname):
            return redirect('/userDeets')
        
        else:
            return render_template('error.html', message = 'It did not update')
    else:
        return redirect('/')
'''
@app.route('/basket')
def basketView():
    # basket = Basket()
    basket = session.get('basket')

    if basket is None:
        basket = Basket()
        session['basket'] = basket
    # basket = session['basket']
    totalPrice = basket.basketTotal()
    return render_template('basket.html', basket=basket.viewBasket(), totalPrice = totalPrice)
'''
@app.route('/addBook', methods=['POST'])
def addToBasket():
    title = request.form['title']
    author = request.form['author']
    isbn = request.form['isbn']
    price = float(request.form['price'])
    overview = request.form['overview']
    
    book = Book(title, author, isbn, price, overview)
    
    basketData = session.get('basket')
    
    if basketData:
        basket = Basket.fromDictToList(basketData)
    else:
        basket = Basket()
    
    basket.addBook(book)
    
    session['basket'] = basket.fromListToDict()
    
    return redirect('/basket')

@app.route('/basket')
def basketView():
    basketData = session.get('basket')
    if basketData:
        basket = Basket.fromDictToList(basketData)
        totalPrice = basket.basketTotal()
        return render_template('basket.html', basket=basket.viewBasket(), totalPrice=totalPrice)
    else:
        return render_template('basket.html', basket=[], totalPrice=0)

@app.route('/removeBook', methods=['POST'])
def removeFromBasket():
    isbn = request.form['isbn']
    
    basketData = session.get('basket')
    
    if basketData:
        basket = Basket.fromDictToList(basketData)
        removeBook = next((book for book in basket.items if book.isbn == isbn), None)
        if removeBook:
            basket.removeBook(removeBook)
            session['basket'] = basket.fromListToDict()
            
    return redirect('/basket')

@app.route('/checkout', methods=['POST'])
def checkout():
    if 'email' in session:
        email = session['email']
        basketData = session.get('basket')
        print(basketData)
        if basketData:
            # basket = Basket.fromDictToList({'items': basketData})
            # print(basket)
            with open('orders.txt', 'a') as file:
                for book in basketData.items:
                    print(book.title)
                    file.write(f'{email},{book.title},{book.author},{book.isbn},{book.price}\n')
            session.pop('basket', None)
        return redirect('/basket') # render_template('error.html', message = 'still not working') 
    else:
        return render_template('login.html', message = 'Please log in before buying')
    


'''
@app.route('/basket')
def basketView():
    basketData = session.get('basket', [])
    basket = Basket.fromDictToList({'items': basketData})
    
    totalPrice = basket.basketTotal()
    
    return render_template('basket.html', basket=basket.viewBasket(), totalPrice=totalPrice)


@app.route('/addBook', methods=['POST'])
def addToBasket():
    title = request.form['title']
    author = request.form['author']
    isbn = request.form['isbn']
    price = float(request.form['price'])
    overview = request.form['overview']
    
    book = Book(title, author, isbn, price, overview)
    
    basketData = session.get('basket', [])
    # checking if the data is a list or a dict and adjusting to account for it
    if isinstance(basketData, list):
        basketData.append(book.__dict__)
    else:
        basketData['items'].append(book.__dict__)
    
    session['basket'] = basketData
    return redirect('/basket')
    
'''
'''
    if basketData:
        basket = Basket.fromDictToList(basketData)
    else:
        basket = Basket()
    
    basket.addBook(book)
    
    session['basket'] = basket.fromListToDict()
'''
    
    # return render_template('basket.html', backet = basket.viewBasket)

if __name__ == '__main__':
    app.run(debug=True)
    
    
