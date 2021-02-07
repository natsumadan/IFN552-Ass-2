from flask import Blueprint, render_template, url_for, request, session, flash, redirect
from .models import Product, Item, Order
from datetime import datetime
from .forms import CheckoutForm
from . import db


bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    product = Product.query.order_by(Product.name).all()
    return render_template('index.html', product = product)

@bp.route('/item/<int:productid>/')
def items(productid):
    item = Item.query.filter(Item.product_id == productid)
    return render_template('products.html', item = item)

@bp.route('/item/')
def search():
    search= request.args.get('search')
    search = '%{}%'.format(search)
    item = Item.query.filter(Item.description.like(search)).all()
    return render_template('products.html', item = item)


# Referred to as "Basket" to the user
@bp.route('/order', methods=['POST','GET'])
def order():
    item_id = request.values.get('item_id')
    # retrieve order if there is one
    if 'order_id'in session.keys():
        order = Order.query.get(session['order_id'])
        # order will be None if order_id stale
    else:
        # there is no order
        order = None

    # create new order if needed
    if order is None:
        order = Order(status = False, firstname='', surname='', email='', phone='', totalcost=0, date=datetime.now())
        try:
            db.session.add(order)
            db.session.commit()
            session['order_id'] = order.id
        except:
            print('failed at creating a new order')
            order = None
    
    # calcultate totalprice
    totalprice = 0
    if order is not None:
        for item in order.item:
            totalprice = totalprice + item.price
    
    # are we adding an item?
    if item_id is not None and order is not None:
        item = Item.query.get(item_id)
        if item not in order.item:
            try:
                order.item.append(item)
                db.session.commit()
                flash('item Added to the cart')
            except:
                return 'There was an issue adding the item to your basket'
            return redirect(url_for('main.order'))
        else:
            flash('item already in Cart')
            return redirect(url_for('main.order'))
    
    return render_template('order.html', order = order, totalprice = totalprice)


# Delete specific basket items
@bp.route('/deleteorderitem', methods=['POST'])
def deleteorderitem():
    id=request.form['id']
    if 'order_id' in session:
        order = Order.query.get_or_404(session['order_id'])
        tour_to_delete = Item.query.get(id)
        try:
            order.item.remove(tour_to_delete)
            db.session.commit()
            flash('item deleted')
            return redirect(url_for('main.order'))
            
        except:
            return 'Problem deleting item from order'
    return redirect(url_for('main.order'))


# Scrap basket
@bp.route('/deleteorder')
def deleteorder():
    if 'order_id' in session:
        del session['order_id']
        flash('All items deleted')
    return redirect(url_for('main.index'))


@bp.route('/checkout', methods=['POST','GET'])
def checkout():
    form = CheckoutForm() 
    if 'order_id' in session:
        order = Order.query.get_or_404(session['order_id'])
       
        if form.validate_on_submit():
            order.status = True
            order.firstname = form.firstname.data
            order.surname = form.surname.data
            order.email = form.email.data
            order.phone = form.phone.data
            totalcost = 0
            for item in order.item:
                totalcost = totalcost + item.price
            order.totalcost = totalcost
            order.date = datetime.now()
            try:
                db.session.commit()
                del session['order_id']
                flash('Thank you! One of our awesome team members will contact you soon...')
                return redirect(url_for('main.index'))
            except:
                return 'There was an issue completing your order'
    return render_template('checkout.html', form = form)