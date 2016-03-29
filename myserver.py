'''
Project1 part3 Shanqi Lu
psql -U sl4017 -h w4111db.eastus.cloudapp.azure.com
'''

import os, datetime,time
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, session, render_template, g, redirect, Response, flash, url_for


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

app.config.update(dict(
    SECRET_KEY='development key',
))



#DATABASEURI = "sqlite:///test.db"
DATABASEURI = "postgresql://sl4017:YUVVRS@w4111db.eastus.cloudapp.azure.com/sl4017"

engine = create_engine(DATABASEURI)


def IsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def Isdate(date_text):
    try:
        a = datetime.datetime.strptime(date_text, '%Y-%m-%d')
        p = datetime.datetime.now()
        if a <= p:
            return False
        else:
            return True
    except ValueError:
        return False
def IsName(my_string):
    return all(i.isalpha() or i.isspace() for i in my_string)

def IsStar(s):
    try: 
        int(s)
        if int(s)<6 and int(s)>0:
            return True
        else:
            return False
    except ValueError:
        return False

def IsRating(s):
    try: 
        int(s)
        if int(s)<11 and int(s)>0:
            return True
        else:
            return False
    except ValueError:
        return False


@app.before_request
def before_request():

  try:
    g.conn = engine.connect()
    print ('Connected to my database!')
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):

  try:
    g.conn.close()
    print ('Disconnected from my database!')
  except Exception as e:
    pass


@app.route('/', methods=['GET', 'POST'])
def index():

  # DEBUG: this is debugging code to see what request looks like
  print request.args
  cid_tmp = session.get('cid')
  defaultpay = session.get('defaultpay')
  if cid_tmp is not None and session.get('logged_in') is not None:


    if request.method == 'POST':
        #~~~~~~~~~~~~~~~~Show All Products~~~~~~~~~~~~~~~~~~~
        if request.form.get("subject", None) == "Show All Products":
            cursor = g.conn.execute("SELECT * FROM laptops_soldby;")
            laptops = cursor.fetchall()

            return render_template('index.html', cid = str(session['cid']), laptops = laptops)
        
        elif request.form.get("subject", None) == "Hide All":
            return render_template('index.html', cid = str(session['cid']))

        elif request.form.get("subject2",None)=="Add Laptop to Cart":
            cursor = g.conn.execute("SELECT * FROM laptops_soldby;")
            laptops = cursor.fetchall()

            cartlaptopid = request.form.get("subject2cartlaptopid",None)

            laptopid_exists = False
            for laptop in laptops:
                if str(cartlaptopid) == str(laptop.lid):
                    laptopid_exists = True
            if laptopid_exists == False:
                addcart_notice = "Cannot find this Laptop!"
                return render_template('index.html', cid = str(session['cid']), laptops = laptops, addcart_notice =  addcart_notice)
            else:
                
                cursor = g.conn.execute("select i.lid from incart i where i.cid=(%s);", str(cid_tmp))
                laptops_incart = cursor.fetchall()
                already_incart = False
                for laptop_incart in laptops_incart:
                    if str(cartlaptopid) == str(laptop_incart.lid):
                        already_incart = True
                
                if already_incart == True:
                    q = "update incart i set cartquantity =cartquantity+1"\
                    " where i.cid = (%s) and i.lid = (%s);"
                    values = (str(cid_tmp), str(cartlaptopid))
                    g.conn.execute(q, values)
                else:
                    q = "insert into incart values(%s, %s, %s)"
                    values = (str(cartlaptopid), str(cid_tmp), "1")
                    g.conn.execute(q, values)

                addcart_notice = "Success!\n You can go to your Shopping Cart and Check out! "
                return render_template('index.html', cid = str(session['cid']), laptops = laptops, addcart_notice = addcart_notice)

        #~~~~~~~~~~~~~~~~Show All Products~~~~~~~~~~~~~~~~~~~

        #~~~~~~~~~~~~~~~~My Payment Methods~~~~~~~~~~~~~~~~
        elif request.form.get("subject", None) == "My Payment Methods":
            value = str(cid_tmp)
            cursor = g.conn.execute("select p.cardnumber,p.cardholder,p.expirydate from paymethods p, addpay a"\
            " where a.cid = (%s) and  p.cardnumber= a.cardnumber;", value)     
            paymethods = cursor.fetchall()
            
            return render_template('index.html', cid = str(session['cid']), paymethods = paymethods, defaultpay = defaultpay)
        elif request.form.get("subject2",None)=="Add Payment Method":
            value = str(cid_tmp)
            cursor = g.conn.execute("select p.cardnumber,p.cardholder,p.expirydate from paymethods p, addpay a"\
            " where a.cid = (%s) and  p.cardnumber= a.cardnumber;", value)     
            paymethods = cursor.fetchall()

            cardnumber = request.form.get("subject2cardnumber",None)
            cardholder = request.form.get("subject2cardholder",None)
            expirydate = request.form.get("subject2expirydate",None)

            if cardnumber == None or IsInt(str(cardnumber)) == False or len(str(cardnumber))!= 16:
                addpay_notice = "Please enter a correct cardnumber(16-digit)"
            else:
                card_exists = False
                for paymethod in paymethods:
                    if str(cardnumber)==str(paymethod.cardnumber):
                        card_exists = True
                if card_exists == True:
                    addpay_notice = "This card already exists" 
                elif cardholder == None or IsName(str(cardholder))==False:
                    addpay_notice = "Please enter a correct cardholder"
                elif expirydate == None or Isdate(str(expirydate)) == False:
                    addpay_notice = "Please enter a correct expirydate"
                else: 
                    
                    q= "select * from paymethods"
                    cursor = g.conn.execute(q)
                    existed_cards = cursor.fetchall() 
                    cardnumber_existed = False

                    for i in existed_cards:
                        if str(cardnumber) == i.cardnumber:
                            cardnumber_existed = True

                    if cardnumber_existed==False:
                        values =  (str(cardnumber), str(cardholder) , str(expirydate))
                        q = "insert into paymethods values(%s, %s, %s)"
                        g.conn.execute(q, values)

                    values = (str(cardnumber), str(cid_tmp))
                    q = "insert into addpay values(%s, %s)"
                    g.conn.execute(q, values)
                    
                    value = str(cid_tmp)
                    cursor = g.conn.execute("select p.cardnumber,p.cardholder,p.expirydate from paymethods p, addpay a"\
                    " where a.cid = (%s) and  p.cardnumber= a.cardnumber;", value)     
                    paymethods = cursor.fetchall()
                    
                    addpay_notice = "Success!"
                    return render_template('index.html', cid = str(session['cid']), paymethods = paymethods,addpay_notice = addpay_notice,defaultpay = defaultpay)

            return render_template('index.html', cid = str(session['cid']), paymethods = paymethods,addpay_notice =addpay_notice,defaultpay = defaultpay)

        elif request.form.get("subject2",None)=="Change Default Payment Method":
            value = str(cid_tmp)
            cursor = g.conn.execute("select p.cardnumber,p.cardholder,p.expirydate from paymethods p, addpay a"\
            " where a.cid = (%s) and  p.cardnumber= a.cardnumber;", value)     
            paymethods = cursor.fetchall()


            changeto = request.form.get("subject2changeto")
            changeto_exists = False
            for paymethod in paymethods:
                if str(changeto) == str(paymethod.cardnumber):
                    changeto_exists = True

            if changeto_exists == False:
                changepay_notice = "Cannot find this card! Please enter a correct cardnumber"
                return render_template('index.html', cid = str(session['cid']), paymethods = paymethods, defaultpay = defaultpay, changepay_notice=changepay_notice)
            else:
                session["defaultpay"] = str(changeto)
                defaultpay = str(changeto)
                changepay_notice = "Success!"
                return render_template('index.html', cid = str(session['cid']), paymethods = paymethods, defaultpay = defaultpay, changepay_notice= changepay_notice)
        
        
        elif request.form.get("subject2",None)=="Delete this card":
            value = str(cid_tmp)
            cursor = g.conn.execute("select p.cardnumber,p.cardholder,p.expirydate from paymethods p, addpay a"\
            " where a.cid = (%s) and  p.cardnumber= a.cardnumber;", value)     
            paymethods = cursor.fetchall()

            deletecard = request.form.get("subject2deletecard")
            deletecard_exists = False
            no_cards = 0
            for paymethod in paymethods:
                no_cards = no_cards+1
                if str(deletecard) ==str(paymethod.cardnumber):
                    deletecard_exists = True
            if deletecard_exists == False:
                deletecard_notice = "Cannot find this card!"
            elif no_cards == 1:
                deletecard_notice = "Cannot delete. You only have one card!"
            else:

                q = "delete from addpay a where a.cardnumber = (%s) and a.cid = (%s) "
                values = (str(deletecard), str(cid_tmp))
                g.conn.execute(q, values)

                
                q= "select a.cardnumber from addpay a where a.cid = (%s) limit 1;"
                value = str(session['cid'])
                cursor = g.conn.execute(q, value)
                defaultpay = cursor.fetchone().cardnumber
                session['defaultpay'] = str(defaultpay)

                value = str(cid_tmp)
                cursor = g.conn.execute("select p.cardnumber,p.cardholder,p.expirydate from paymethods p, addpay a"\
                " where a.cid = (%s) and  p.cardnumber= a.cardnumber;", value)     
                paymethods = cursor.fetchall()

                deletecard_notice = "This card is successfully deleted!"
                return render_template('index.html', cid = str(session['cid']), paymethods = paymethods, defaultpay = defaultpay, deletecard_notice= deletecard_notice)

            return render_template('index.html', cid = str(session['cid']), paymethods = paymethods, defaultpay = defaultpay, deletecard_notice= deletecard_notice)
        #~~~~~~~~~~~~~~~~My Payment Methods~~~~~~~~~~~~~~~~
        

        #~~~~~~~~~~~~~~~~My Orders~~~~~~~~~~~~~~~~
        elif request.form.get("subject", None) == "My Orders":
            value = str(cid_tmp)
            cursor = g.conn.execute("select o.orid, o.ordate, o.cardnumber, o.paiddate, sum(l.price*list.listquantity) as total_price "\
            "from laptops_soldby l, orders_paidby o, customers c, place p, lists list "\
            "where c.cid = (%s) and p.cid= c.cid and p.orid = o.orid and list.orid = o.orid and list.lid = l.lid "\
            "group by o.orid, o.ordate, o.cardnumber, o.paiddate;", value)     
            orders = cursor.fetchall()
            
            return render_template('index.html', cid = str(session['cid']), orders = orders) 
        
        elif request.form.get("subject2oid",None) is not None and request.form.get("subject2",None)=="Show Oder Details":
            value = str(cid_tmp)
            cursor = g.conn.execute("select o.orid, o.ordate, o.cardnumber, o.paiddate, sum(l.price*list.listquantity) as total_price "\
            "from laptops_soldby l, orders_paidby o, customers c, place p, lists list "\
            "where c.cid = (%s) and p.cid= c.cid and p.orid = o.orid and list.orid = o.orid and list.lid = l.lid "\
            "group by o.orid, o.ordate, o.cardnumber, o.paiddate;", value)     
            orders = cursor.fetchall()

            myorder_list = []
            for order in orders:
                myorder_list.append(order.orid)
            
            ismyorder = False
            for i in range (0, len(myorder_list)):
                if str(myorder_list[i]) == str(request.form.get("subject2oid",None)):
                    ismyorder = True

            if ismyorder == False:
                myorder_error = "This is not your order!"
                return render_template('index.html', cid = str(session['cid']), orders = orders, myorder_error = myorder_error)
            else:
                myorder_error  = None
                value = str(request.form.get("subject2oid",None))
                cursor = g.conn.execute("select l.lid, l.model, l.price, list.listquantity"\
                " from laptops_soldby l, orders_paidby o, lists list"\
                " where o.orid = (%s) and list.orid = o.orid and list.lid = l.lid;", value)
                order_laptops = cursor.fetchall()

                return render_template('index.html', cid = str(session['cid']), orders = orders, order_laptops = order_laptops) 
        #~~~~~~~~~~~~~~~~CF~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif request.form.get("subject2",None)=="Leave comments and feedbacks":

            oidforcf = request.form.get("subject2oidforcf",None)
            session["oidforcf"] = str(oidforcf)

            value = str(cid_tmp)
            cursor = g.conn.execute("select o.orid, o.ordate, o.cardnumber, o.paiddate, sum(l.price*list.listquantity) as total_price "\
            "from laptops_soldby l, orders_paidby o, customers c, place p, lists list "\
            "where c.cid = (%s) and p.cid= c.cid and p.orid = o.orid and list.orid = o.orid and list.lid = l.lid "\
            "group by o.orid, o.ordate, o.cardnumber, o.paiddate;", value)     
            orders = cursor.fetchall()

            oid_exists = False
            for order in orders:
                if str(oidforcf) == str(order.orid):
                    oid_exists = True
            if oid_exists == False:
                cf_notice = "Cannot find this order!"
                return render_template('index.html', cid = str(session['cid']), orders = orders , cf_notice = cf_notice) 
            else:
                q = "select o.orid, o.ordate, o.cardnumber, o.paiddate, sum(l.price*list.listquantity) as total_price"\
                " from laptops_soldby l, orders_paidby o,  lists list "\
                " where o.orid = (%s) and list.orid = o.orid and list.lid = l.lid "\
                " group by o.orid, o.ordate, o.cardnumber, o.paiddate;"
                value = str(oidforcf)
                cursor = g.conn.execute(q, value)
                cforder = cursor.fetchone()
                
                q = "select l.lid, l.model, l.price, list.listquantity, l.sid, s.sname"\
                " from laptops_soldby l, orders_paidby o, lists list, seller s"\
                " where o.orid = (%s) and list.orid = o.orid and list.lid = l.lid and l.sid = s.sid;"
                value = str(oidforcf)
                cursor = g.conn.execute(q, value)
                cflaptops = cursor.fetchall()

                cfinputs = True
                return render_template('index.html', cid = str(session['cid']), cforder = cforder , cflaptops = cflaptops, cfinputs = cfinputs)
        #~~~~~~~~~~~~~~~~Comment~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif request.form.get("subject2",None)=="Leave a comment to this laptop":
                
            oidforcf = session.get("oidforcf")

            q = "select o.orid, o.ordate, o.cardnumber, o.paiddate, sum(l.price*list.listquantity) as total_price"\
            " from laptops_soldby l, orders_paidby o,  lists list "\
            " where o.orid = (%s) and list.orid = o.orid and list.lid = l.lid "\
            " group by o.orid, o.ordate, o.cardnumber, o.paiddate;"
            value = str(oidforcf)
            cursor = g.conn.execute(q, value)
            cforder = cursor.fetchone()
            
            q = "select l.lid, l.model, l.price, list.listquantity, l.sid, s.sname"\
            " from laptops_soldby l, orders_paidby o, lists list, seller s"\
            " where o.orid = (%s) and list.orid = o.orid and list.lid = l.lid and l.sid = s.sid;"
            value = str(oidforcf)
            cursor = g.conn.execute(q, value)
            cflaptops = cursor.fetchall()



            q = "select l.lid, l.sid from orders_paidby o, lists list, laptops_soldby l"\
            " where  o.orid =(%s) and list.orid= o.orid and list.lid= l.lid;"
            value = session.get("oidforcf")
            cursor = g.conn.execute(q, value)

            lidforcf = request.form.get("subject2lidforcf",None)
            lidforcf_exists = False
            for  i in cursor.fetchall():
                if str(lidforcf)==str(i.lid):
                    lidforcf_exists =True
            if lidforcf_exists == False:
                cfinputs = True
                gotoc_notice = "Cannot find this laptop in this order!"
                return render_template('index.html', cid = str(session['cid']), cforder = cforder , cflaptops = cflaptops,cfinputs = cfinputs, gotoc_notice=gotoc_notice)
            else:
                gotocflag = str(lidforcf)
                session["lidforcf"] = str(lidforcf)
                return render_template('index.html', cid = str(session['cid']), cforder = cforder , cflaptops = cflaptops,gotocflag = gotocflag)
        
        elif request.form.get("subject2",None)=="Submit the comment":
            
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            oidforcf = session.get("oidforcf")

            q = "select o.orid, o.ordate, o.cardnumber, o.paiddate, sum(l.price*list.listquantity) as total_price"\
            " from laptops_soldby l, orders_paidby o,  lists list "\
            " where o.orid = (%s) and list.orid = o.orid and list.lid = l.lid "\
            " group by o.orid, o.ordate, o.cardnumber, o.paiddate;"
            value = str(oidforcf)
            cursor = g.conn.execute(q, value)
            cforder = cursor.fetchone()
            
            q = "select l.lid, l.model, l.price, list.listquantity, l.sid, s.sname"\
            " from laptops_soldby l, orders_paidby o, lists list, seller s"\
            " where o.orid = (%s) and list.orid = o.orid and list.lid = l.lid and l.sid = s.sid;"
            value = str(oidforcf)
            cursor = g.conn.execute(q, value)
            cflaptops = cursor.fetchall()

            gotocflag = session["lidforcf"]
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

            star = str(request.form.get("star",None))
            comment = str(request.form.get("comment", None))
            if IsStar(star)== False:
                cfsubmit_notice = "Please enter a correct rating number(integer from 1 to 5)"
                return render_template('index.html', cid = str(session['cid']), cforder = cforder , cflaptops = cflaptops,gotocflag = gotocflag, cfsubmit_notice = cfsubmit_notice)
            else:
                q= "select max(c.commentid) from comments_combine c;"
                cursor = g.conn.execute(q)
                new_comid = str(cursor.fetchone().max + 1)
                new_content = comment
                new_star = star
                new_cid = str(cid_tmp)
                new_lid = gotocflag

                q = "insert into comments_combine values (%s,%s,%s,%s,%s)"
                values=(new_comid, new_content,new_star, new_cid, new_lid)
                g.conn.execute(q,values)

                cfsubmit_notice = "You have successfully submitted a comment! Check it in comments and feedbacks section!"

                return render_template('index.html', cid = str(session['cid']), cforder = cforder , cflaptops = cflaptops, gotocflag = gotocflag, cfsubmit_notice = cfsubmit_notice)

        #~~~~~~~~~~~~~~~~feedback~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif request.form.get("subject2",None)=="Leave a feedback to this seller":
            oidforcf = session.get("oidforcf")

            q = "select o.orid, o.ordate, o.cardnumber, o.paiddate, sum(l.price*list.listquantity) as total_price"\
            " from laptops_soldby l, orders_paidby o,  lists list "\
            " where o.orid = (%s) and list.orid = o.orid and list.lid = l.lid "\
            " group by o.orid, o.ordate, o.cardnumber, o.paiddate;"
            value = str(oidforcf)
            cursor = g.conn.execute(q, value)
            cforder = cursor.fetchone()
            
            q = "select l.lid, l.model, l.price, list.listquantity, l.sid, s.sname"\
            " from laptops_soldby l, orders_paidby o, lists list, seller s"\
            " where o.orid = (%s) and list.orid = o.orid and list.lid = l.lid and l.sid = s.sid;"
            value = str(oidforcf)
            cursor = g.conn.execute(q, value)
            cflaptops = cursor.fetchall()



            q = "select l.lid, l.sid from orders_paidby o, lists list, laptops_soldby l"\
            " where  o.orid =(%s) and list.orid= o.orid and list.lid= l.lid;"
            value = session.get("oidforcf")
            cursor = g.conn.execute(q, value)

            sidforcf = request.form.get("subject2sidforcf",None)
            sidforcf_exists = False
            for  i in cursor.fetchall():
                if str(sidforcf)==str(i.sid):
                    sidforcf_exists =True
            if sidforcf_exists == False:
                cfinputs = True
                gotof_notice = "Cannot find this Seller in this order!"
                return render_template('index.html', cid = str(session['cid']), cforder = cforder , cflaptops = cflaptops, cfinputs = cfinputs,gotof_notice=gotof_notice)
            else:
                gotofflag = str(sidforcf)
                session["sidforcf"] = str(sidforcf)
                return render_template('index.html', cid = str(session['cid']), cforder = cforder , cflaptops = cflaptops, gotofflag=gotofflag)

        elif request.form.get("subject2",None)=="Submit the feedback":
            
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            oidforcf = session.get("oidforcf")

            q = "select o.orid, o.ordate, o.cardnumber, o.paiddate, sum(l.price*list.listquantity) as total_price"\
            " from laptops_soldby l, orders_paidby o,  lists list "\
            " where o.orid = (%s) and list.orid = o.orid and list.lid = l.lid "\
            " group by o.orid, o.ordate, o.cardnumber, o.paiddate;"
            value = str(oidforcf)
            cursor = g.conn.execute(q, value)
            cforder = cursor.fetchone()
            
            q = "select l.lid, l.model, l.price, list.listquantity, l.sid, s.sname"\
            " from laptops_soldby l, orders_paidby o, lists list, seller s"\
            " where o.orid = (%s) and list.orid = o.orid and list.lid = l.lid and l.sid = s.sid;"
            value = str(oidforcf)
            cursor = g.conn.execute(q, value)
            cflaptops = cursor.fetchall()

            gotofflag = session["sidforcf"]
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

            deliveryspeed = str(request.form.get("deliveryspeed",None))
            productquality = str(request.form.get("productquality",None))
            feedback = str(request.form.get("feedback",None))

            if IsRating(deliveryspeed)== False or IsRating(productquality) == False:
                cfsubmit_notice = "Please enter a correct rating number(integer from 1 to 5)"
                return render_template('index.html', cid = str(session['cid']), cforder = cforder , cflaptops = cflaptops,gotocflag = gotocflag, cfsubmit_notice = cfsubmit_notice)
            else:
                q= "select max(f.feedbackid) from feedback_combine f;"
                cursor = g.conn.execute(q)
                new_feedbackid = str(cursor.fetchone().max + 1)
                new_deliveryspeed = deliveryspeed
                new_productquality = productquality
                new_feedback = feedback
                new_cid = str(cid_tmp)
                new_sid = gotofflag

                q = "insert into feedback_combine values (%s,%s,%s,%s,%s, %s)"
                values=(new_feedbackid, new_deliveryspeed,new_productquality, new_feedback, new_cid,new_sid)
                g.conn.execute(q,values)

                cfsubmit_notice = "You have successfully submitted a feedback! Check it in comments and feedbacks section!"

                return render_template('index.html', cid = str(session['cid']), cforder = cforder , cflaptops = cflaptops, gotofflag = gotofflag, cfsubmit_notice = cfsubmit_notice)

        #~~~~~~~~~~~~~~~~feedback~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        #~~~~~~~~~~~~~~~~My Orders~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        #~~~~~~~~~~~~~~~~My Shopping Cart~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif request.form.get("subject", None) == "My Shopping Cart":
            value = str(cid_tmp)
            cursor = g.conn.execute("select l.lid, l.model, l.price, i.cartquantity"\
            " from laptops_soldby l, customers c, incart i"\
            "  where c.cid = (%s) and c.cid = i.cid and i.lid = l.lid;", value)     
            cart_laptops = cursor.fetchall()
            
            return render_template('index.html', cid = str(session['cid']), cart_laptops = cart_laptops )         

        elif request.form.get("subject2", None) == "Proceed to checkout":
            value = str(cid_tmp)
            cursor = g.conn.execute("select l.lid, l.model, l.price, i.cartquantity"\
            " from laptops_soldby l, customers c, incart i"\
            "  where c.cid = (%s) and c.cid = i.cid and i.lid = l.lid;", value)     
            cart_laptops = cursor.fetchall()

            proceed = True

            return render_template('index.html', cid = str(session['cid']), cart_laptops = cart_laptops,proceed=proceed,defaultpay = defaultpay)
        
        elif request.form.get("subject2", None) == "Place your order":

            q= "select max(o.orid) from orders_paidby o;"
            cursor = g.conn.execute(q)

            new_orid = str(cursor.fetchone().max + 1)
            new_cardnumber = session.get("defaultpay")
            new_ordate = time.strftime('%Y-%m-%d')
            new_paiddate = new_ordate

            q = "insert into orders_paidby values(%s, %s, %s, %s)"
            values = (new_orid,new_cardnumber,new_paiddate,new_ordate)
            g.conn.execute(q, values)

            q = "insert into place values(%s, %s)"
            values = (new_orid, str(cid_tmp))
            g.conn.execute(q, values)


            value = str(cid_tmp)
            cursor = g.conn.execute("select l.lid, i.cartquantity"\
            " from laptops_soldby l, customers c, incart i"\
            "  where c.cid = (%s) and c.cid = i.cid and i.lid = l.lid;", value)     
            cart_laptops = cursor.fetchall()
            for cart_laptop in cart_laptops:
                q = "insert into lists values(%s, %s, %s)"
                values = (new_orid, str(cart_laptop.lid), str(cart_laptop.cartquantity) )
                g.conn.execute(q, values)

            q = "delete from incart i where i.cid = (%s);"
            value = str(cid_tmp)
            g.conn.execute(q, value)

            notice = "You have placed your order! \n Please check the result in My Orders section!"
            return render_template('index.html', cid = str(session['cid']), notice = notice)

        elif request.form.get("subject2", None) == "Delete this item":
            value = str(cid_tmp)
            cursor = g.conn.execute("select l.lid, l.model, l.price, i.cartquantity"\
            " from laptops_soldby l, customers c, incart i"\
            "  where c.cid = (%s) and c.cid = i.cid and i.lid = l.lid;", value)     
            cart_laptops = cursor.fetchall()

            cartdelete = request.form.get("subject2cartdelete", None)
            delete_exists = False
            for cart_laptop in cart_laptops:
                if str(cartdelete) == str(cart_laptop.lid):
                    delete_exists = True

            if delete_exists == False:
                cartdelete_notice = 'This item is not in your Shopping Cart!'
                return render_template('index.html', cid = str(session['cid']), cart_laptops = cart_laptops, cartdelete_notice= cartdelete_notice ) 
            else:
                
                q = "delete from incart i where i.cid = (%s) and i.lid = (%s);"
                values = (str(cid_tmp), str(cartdelete))
                g.conn.execute(q, values)

                value = str(cid_tmp)
                cursor = g.conn.execute("select l.lid, l.model, l.price, i.cartquantity"\
                " from laptops_soldby l, customers c, incart i"\
                "  where c.cid = (%s) and c.cid = i.cid and i.lid = l.lid;", value)     
                cart_laptops = cursor.fetchall()

                cartdelete_notice = 'This item is deleted from your Shopping Cart!'
                return render_template('index.html', cid = str(session['cid']), cart_laptops = cart_laptops, cartdelete_notice= cartdelete_notice ) 
        #~~~~~~~~~~~~~~~~My Shopping Cart~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


        #~~~~~~~~~~~~~~~~Comments and Feedbacks~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        elif request.form.get("subject", None) == "Comments and Feedbacks":

            cf = True
            return render_template('index.html', cid = str(session['cid']), cf = cf) 

        elif request.form.get("subject2", None) == "Show comments":
            cf = True
            cursor = g.conn.execute("SELECT * FROM laptops_soldby;")
            laptops = cursor.fetchall()
            lid_comments = request.form.get("subject2comments", None)

            laptopid_exists = False
            for laptop in laptops:
                if str(lid_comments) == str(laptop.lid):
                    laptopid_exists = True
            if laptopid_exists == False:
                comment_notice = "Cannot find this laptop!"
                return render_template('index.html', cid = str(session['cid']), cf = cf, comment_notice = comment_notice)
            else:
                q = "select com.star,com.content, c.name"\
                " from comments_combine com, customers c"\
                " where com.lid = (%s) and com.cid = c.cid;"
                value = str(lid_comments)
                cursor = g.conn.execute(q, value)
                comments = cursor.fetchall()

                q = "select s.sid, s.sname from laptops_soldby l,seller s"\
                " where l.lid = (%s) and l.sid=s.sid;"
                value = str(lid_comments)
                cursor = g.conn.execute(q, value)
                seller = cursor.fetchone()

                q = "select f.deliveryspeed, f.productquality, f.feedbackcontent, c.name"\
                " from laptops_soldby l, seller s, feedback_combine f, customers c"\
                " where l.lid =(%s) and l.sid = s.sid and f.sid = s.sid and c.cid=f.cid;"
                value = str(lid_comments)
                cursor = g.conn.execute(q, value)
                feedbacks = cursor.fetchall()

                return render_template('index.html', cid = str(session['cid']), cf = cf, comments = comments,seller=seller,feedbacks = feedbacks)
         
        elif request.form.get("subject2", None) == "Show my comments and feedbacks":
            cf = True
            show_my_cf = True
            q= "select c.star, c.content,c.lid, l.model"\
            " from comments_combine c, laptops_soldby l"\
            " where c.cid =(%s) and c.lid = l.lid;"
            value = str(cid_tmp)
            cursor = g.conn.execute(q, value)
            my_comments = cursor.fetchall()

            q= "select f.deliveryspeed, f.productquality, f.feedbackcontent, f.sid, s.sname"\
            " from feedback_combine f, seller s"\
            " where f.cid = (%s) and f.sid= s.sid;"
            cursor = g.conn.execute(q, value)
            my_feedbacks = cursor.fetchall()

            return render_template('index.html', cid = str(session['cid']), cf = cf, show_my_cf =show_my_cf, my_comments= my_comments, my_feedbacks=my_feedbacks) 
        #~~~~~~~~~~~~~~~~Comments and Feedbacks~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        else:
            return render_template('index.html', cid = str(session['cid']))
    else:
        return render_template("index.html", cid = str(session['cid']))
  else:
    return render_template("index.html")

#~~~~~~~~~~~~~~~~Sign up ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    cursor = g.conn.execute("SELECT cid FROM customers")
    results = cursor.fetchall()
    cid_list = []
    for result in results:
        cid_list.append(result.cid)
    cursor.close

    if request.method == 'POST':
        for i in range(0, len(cid_list)):
            if str(request.form['cid']) == str(cid_list[i]):
                error = 'Customer ID already exists'
                return render_template("signup.html", error = error)
        if request.form['cid'] == '':
            error = 'Please enter Customer ID'
        elif IsInt(str(request.form['cid']))==False:
            error = 'Please enter a valid Customer ID which must be int'
        
        elif request.form['password'] == '':
            error = 'Please enter password'
        elif request.form['name'] == '' or IsName(str(request.form['name']))== False:
            error = 'Please enter a correct name'
        
        elif request.form['cardnumber'] == '':
            error = 'Please enter your credit card number'
        elif IsInt(str(request.form['cardnumber']))==False or len(str(request.form['cardnumber']))!=16:
            error = 'Please enter a valid cardnumber which must be 16-digit int'
        
        elif request.form['cardholder'] == '' or IsName(str(request.form['cardholder']))== False:
            error = 'Please enter a correct card holder'
        elif request.form['expirydate'] == '':
            error = 'Please enter expirydate'
        elif Isdate(str(request.form['expirydate']))==False:
            error = 'Please enter a correct expirydate'
        

        else:
            
            cid = request.form['cid']
            password = request.form['password']
            name = request.form['name']
            cardnumber = request.form['cardnumber']
            cardholder = request.form['cardholder']
            expirydate = request.form['expirydate']


            values =  (cid, password , name)
            values2 = (cardnumber, cid)
            values3 = (cardnumber, cardholder, expirydate)

            q = "insert into customers values(%s, %s, %s)"
            q2 = "insert into addpay values(%s, %s)"
            q3 = "insert into paymethods values(%s, %s, %s)"
            g.conn.execute(q, values)
            
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            q= "select * from paymethods"
            cursor = g.conn.execute(q)
            existed_cards = cursor.fetchall() 
            cardnumber_existed = False

            for i in existed_cards:
                if str(cardnumber) == i.cardnumber:
                    cardnumber_existed = True

            if cardnumber_existed==False:
                g.conn.execute(q3, values3)
            #~~~~~~~~~~~~~~~~~~~~~~~
            g.conn.execute(q2, values2)
            return render_template("success.html")

    return render_template("signup.html", error = error)
#~~~~~~~~~~~~~~~~Sign up ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#~~~~~~~~~~~~~~~~Login ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    cursor = g.conn.execute("SELECT * FROM customers")
    '''
    entries = cursor.fetchall()
    print entries[1]['cid']
    '''
    cid_list = []
    password_list = []
    for result in cursor:
        cid_list.append(result['cid'])
        password_list.append(result['password'])
    cursor.close

    if request.method == 'POST':
        for i in range(0, len(cid_list)):
            if str(request.form['cid']) == str(cid_list[i]):
                if str(request.form['password']) == str(password_list[i]):

                    session['logged_in'] = True
                    session['cid'] = cid_list[i]


                    q= "select a.cardnumber from addpay a where a.cid = (%s) limit 1;"
                    value = str(session['cid'])
                    cursor = g.conn.execute(q, value)
                    defaultpay = cursor.fetchone().cardnumber
                    session['defaultpay'] = str(defaultpay)

                    return redirect(url_for('index'))
        error = 'Invalid cid or password'
    return render_template('login.html', error=error)
#~~~~~~~~~~~~~~~~Login ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


#~~~~~~~~~~~~~~~~Logout ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@app.route('/logout')
def logout():
    session.pop('logged_in', None)

    return render_template("index.html")
#~~~~~~~~~~~~~~~~Logout ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__ == "__main__":
    import click
    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=8111, type=int)
    def run(debug, threaded, host, port):

        HOST, PORT = host, port
        print "running on %s:%d" % (HOST, PORT)
        app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)
    
    run()
