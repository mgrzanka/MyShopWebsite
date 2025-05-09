from flask import (render_template, redirect, url_for, flash, abort,
                   request, session)
from sqlalchemy import or_
from markupsafe import Markup
from flask_login import login_user, login_required, logout_user, current_user
from shop.login_manager import url_has_allowed_host_and_scheme

from shop import app, db
from shop.models import Item, User, Image
from shop.forms import (RegisterForm, LoginForm, AddToCartForm,
                        ChangeAmountForm, SellForm, SearchForm)
import os
import shutil


@app.route('/home')
@app.route('/', methods=['POST', 'GET'])
def home_page():
    search_form = SearchForm()
    return render_template("index.html", search_form=search_form)


@app.route('/shop', methods=['POST', 'GET'])
@login_required
def shop_page():
    form = AddToCartForm()
    search_form = SearchForm()

    if request.method == "POST":
        item_id = request.form['purchased_item']
        item = Item.query.get(item_id)
        item_amount = form.amount.data
        if form.validate_on_submit():
            if session.get('cart') is None:
                session['cart'] = {}
            session['cart'][item_id] = item_amount
            flash(Markup(f"You added {item.name} (x{item_amount}) to your cart - see it <a href='{url_for('cart_page')}' class='alert-link'> here </a>"),
                  category='success')
            return redirect(url_for('shop_page', per_page=request.args.get('per_page', 10)))
        else:
            flash(f"There was a problem with adding {item.name} to your cart", category='danger')
            return redirect(url_for('shop_page', per_page=request.args.get('per_page', 10)))

    else:
        per_page = request.args.get('per_page', 10, type=int)
        page = request.args.get('page', 1, type=int)
        searched_name = request.args.get('search_name', '')
        query = db.select(Item).where(Item.owner_id != current_user.id)
        if searched_name:
            query = query.where(or_(
                Item.name.ilike(f"%{searched_name}%"),
                Item.category.ilike(f"%{searched_name}%")
            ))

        items = db.paginate(query, page=page, per_page=per_page)
        next_url = url_for('shop_page', page=items.next_num) if items.has_next else None
        prev_url = url_for('shop_page', page=items.prev_num) if items.has_prev else None
        return render_template('shop.html', items=items.items, pages=items.pages, page=items.page,
                               next_url=next_url, prev_url=prev_url,
                               form=form, search_form=search_form)


@app.route('/myitems', methods=["POST", "GET"])
@login_required
def my_items_page():
    if request.method == "POST":
        item_id = request.form['selected_item']
        item = Item.query.get(item_id)
        images = Image.query.filter_by(item_id=item_id).all()
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), app.config['IMG_DIR'], os.path.dirname(images[0].img_src))
        if os.path.exists(path):
            shutil.rmtree(path)
        for img in images:
            db.session.delete(img)
        db.session.delete(item)
        db.session.commit()
        return redirect(url_for('my_items_page'))
    else:
        items = Item.query.filter_by(owner_id=current_user.id).all()
        items_counter = list(range(len(items)))
        return render_template("my_items.html", items=items, items_counter=items_counter, zip=zip)


@app.route('/myitems/edit/<int:id>', methods=['POST', 'GET'])
@login_required
def update_page(id):
    item = Item.query.get(id)
    form = SellForm(obj=item)
    if request.method == "POST":
        if form.validate_on_submit() and form.submit.data:
            item.name = form.name.data
            item.category = form.category.data
            item.price = form.price.data
            item.amount = form.amount.data
            item.description = form.description.data
            add_image(form.img.data, item)
            db.session.commit()
            flash(f"{item.name} was edited", category="info")
            return redirect(url_for("my_items_page"))

    return render_template('sell.html', form=form, item=item)


@app.route('/myitems/delete/<int:item_id>/<int:img_id>', methods=["POST"])
@login_required
def delete_image(item_id, img_id):
    image_to_delete = Image.query.get(img_id)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), app.config['IMG_DIR'], image_to_delete.img_src)
    if os.path.exists(path):
        os.remove(path)
    db.session.delete(image_to_delete)
    db.session.commit()

    return redirect(url_for("update_page", id=item_id))


# TODO: mail with informtion someone bought your item
# TODO: Implement item delivery API
@app.route('/cart', methods=['POST', 'GET'])
@login_required
def cart_page():
    change_amount_form = ChangeAmountForm()
    search_form = SearchForm()
    items = []
    items_amounts = []
    counter_list = []
    counter = 1
    total = 0
    if session.get('cart') is not None:
        items_amounts = list(session['cart'].values())
        items_id = session['cart'].keys()
        for id, amount in zip(items_id, items_amounts):
            item = Item.query.get(id)
            if item:
                items.append(item)
                counter_list.append(counter)
                counter += 1
                total += item.price * amount

    if request.method == 'POST':
        if change_amount_form.validate_on_submit():
            item_id = request.form['selected_item']
            if change_amount_form.minus_submit.data:
                session['cart'][item_id] -= 1
            elif change_amount_form.plus_submit.data:
                session['cart'][item_id] += 1
            else:
                del session['cart'][item_id]

            session.modified = True
            return redirect(url_for('cart_page'))
        else:
            current_user.budget -= total
            for item, item_amount in zip(items, items_amounts):
                if item.amount < item_amount:
                    flash("There are not enough of this item", category="danger")
                else:
                    item.amount -= item_amount
                    if item.amount <= 0:
                        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), app.config['IMG_DIR'], os.path.dirname(item.images[0].img_src))
                        if os.path.exists(path):
                            shutil.rmtree(path)
                        for img in item.images:
                            db.session.delete(img)
                        db.session.delete(item)
                    item.owner.budget += item_amount * item.price
                    del session['cart'][str(item.id)]
            db.session.commit()
            # TODO: mail with informtion someone bought your item
            # TODO: Implement item delivary API
            flash("Thank you for purchasing in our shop :P", category="success")
            return redirect(url_for('home_page'))

    else:
        print(session.get('cart'))
        return render_template('cart.html', items=items, items_amounts=items_amounts,
                               total=total, counter_list=counter_list, zip=zip,
                               change_amount_form=change_amount_form, search_form=search_form)


@app.route('/search', methods=["POST"])
def search_page():
    search_form = SearchForm()
    search_name = search_form.search_input.data
    return redirect(url_for('shop_page', search_name=search_name))


@app.route('/register', methods=['POST', 'GET'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        user_to_create = User(username=form.username.data,
                              email=form.email.data,
                              password=form.password1.data)
        db.session.add(user_to_create)
        db.session.commit()
        login_user(user_to_create)
        flash("You have successfully registered :)", category='success')
        return redirect(url_for('shop_page', per_page=10))

    if form.errors:
        flash("There were problems with creating your account", category='danger')

    return render_template('register.html', form=form, search_form=None)


# TODO: mail verification
@app.route('/login', methods=['POST', 'GET'])
def login_page():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        login_user(user, remember=form.remember_me.data)
        flash("You have successfully logged in :)", category='info')

        next = request.args.get('next')
        if not url_has_allowed_host_and_scheme(next, request.host) and next is not None:
            return abort(400)

        if next is None or not url_has_allowed_host_and_scheme(next, request.host):
            return redirect(url_for('shop_page', per_page=10))
        else:
            return redirect(next)

    if form.errors:
        flash("There were problems with logging into your account", category='danger')

    return render_template('login.html', form=form, search_form=None)


@app.route("/logout")
@login_required
def logout_page():
    try:
        logout_user()
        flash("You have been logged out ;)", category='info')
        return redirect(url_for('home_page', per_page=request.args.get('per_page', 10)))
    except Exception:
        flash("Something went wrong while logging out...", category='danger')
        return redirect(url_for('login_page', per_page=request.args.get('per_page', 10)))


@app.route("/sell", methods=["POST", "GET"])
@login_required
def sell_page():
    form = SellForm()
    if form.validate_on_submit():
        item_to_create = Item(name=form.name.data,
                              category=form.category.data,
                              price=form.price.data,
                              amount=form.amount.data,
                              description=form.description.data,
                              owner_id=current_user.id)
        if item_to_create in current_user.items:
            flash("You already added this item", category="danger")
            return redirect(url_for('sell_page'))
        db.session.add(item_to_create)
        db.session.commit()
        add_image(form.img.data, item_to_create)
        flash(Markup(f"Successfully added your item to our shop - see it <a href='{url_for('my_items_page')}' class='alert-link'>here</a>"), category="success")
        return redirect(url_for('shop_page', per_page=request.args.get('per_page', 10)))

    if form.errors:
        flash("There were problems with adding your item", category='danger')

    return render_template('sell.html', form=form)


# TODO: Adding money
@app.route("/addmoney", methods=["GET", "POST"])
def add_money_page():
    return render_template('add_money.html')


def add_image(images, item):
    upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), app.config['UPLOAD_FOLDER'], str(item.id))
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    for file in images:
        if file:
            image = Image(item_id=item.id, img_src="null")
            db.session.add(image)
            db.session.commit()
            filename = str(image.id) + os.path.splitext(file.filename)[1]
            file_path_absolute = os.path.join(upload_folder, filename)
            file.save(file_path_absolute)
            file_path = os.path.join('product_images', str(item.id), filename)
            image.img_src = file_path
            db.session.commit()
