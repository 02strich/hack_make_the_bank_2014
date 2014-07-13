import urllib
import logging
import json

from flask import Flask, render_template, session, redirect, request, flash
from flask_bootstrap import Bootstrap
from jinja2.utils import soft_unicode

from rauth import OAuth1Service, oauth

app = Flask(__name__)
app.secret_key = 'W0\xb9>\x85\xe8\x8f\x00\x18\x9f\x87\xca\x9a\x9f\xe0np\xa1o\xbf\x9d6Ou'
Bootstrap(app)

CONNECTED_BANKS = {
    'sandbox': {
        'name': 'OBP Sandbox',
        'icon': 'http://www.openbankproject.com/static/images/favicon.png',
        'service': OAuth1Service(
            name='sandbox',
            consumer_key='04nfbwmu1haqbzk31hhwddtj5sersnkoi3y4yd5c',
            consumer_secret='zegkibfedfuhtwxuwosovaoep30d0slu5wgtninf',
            request_token_url='https://apisandbox.openbankproject.com/oauth/initiate',
            access_token_url='https://apisandbox.openbankproject.com/oauth/token',
            authorize_url='https://apisandbox.openbankproject.com/oauth/authorize',
            base_url='https://apisandbox.openbankproject.com/obp/v1.2.1/',
            signature_obj=oauth.HmacSha1Signature),
    },
    'sandbox_2': {
        'name': 'OBP Bank',
        'icon': 'http://www.openbankproject.com/static/images/favicon.png',
        'service': OAuth1Service(
            name='sandbox',
            consumer_key='04nfbwmu1haqbzk31hhwddtj5sersnkoi3y4yd5c',
            consumer_secret='zegkibfedfuhtwxuwosovaoep30d0slu5wgtninf',
            request_token_url='https://apisandbox.openbankproject.com/oauth/initiate',
            access_token_url='https://apisandbox.openbankproject.com/oauth/token',
            authorize_url='https://apisandbox.openbankproject.com/oauth/authorize',
            base_url='https://apisandbox.openbankproject.com/obp/v1.2.1/',
            signature_obj=oauth.HmacSha1Signature),
    },
    'sandbox_3': {
        'name': 'OBP Bank 2',
        'icon': 'http://www.openbankproject.com/static/images/favicon.png',
        'service': OAuth1Service(
            name='sandbox',
            consumer_key='04nfbwmu1haqbzk31hhwddtj5sersnkoi3y4yd5c',
            consumer_secret='zegkibfedfuhtwxuwosovaoep30d0slu5wgtninf',
            request_token_url='https://apisandbox.openbankproject.com/oauth/initiate',
            access_token_url='https://apisandbox.openbankproject.com/oauth/token',
            authorize_url='https://apisandbox.openbankproject.com/oauth/authorize',
            base_url='https://apisandbox.openbankproject.com/obp/v1.2.1/',
            signature_obj=oauth.HmacSha1Signature),
    }



}

MERCHANT_ACCOUNT_ID = '10051978'
MERCHANT_BANK_ID = "rbs"
AMOUNT = '10.00'


@app.route("/")
def index():
    return render_template('index.html', connected_banks=CONNECTED_BANKS)

@app.route("/connect/<bank>")
def connect(bank):
    connect_bank = CONNECTED_BANKS[bank]
    request_token, request_token_secret = connect_bank['service'].get_request_token(method="POST", header_auth=True, params=dict(oauth_callback="http://127.0.0.1:3000/callback"))

    session['bank_name'] = bank
    session['request_token_secret'] = request_token_secret

    return redirect(connect_bank['service'].get_authorize_url(request_token))

@app.route("/callback")
def callback():
    oauth_token = request.args.get('oauth_token')
    access_token, access_token_secret = CONNECTED_BANKS[session.get('bank_name', 'sandbox')]['service'].get_access_token(request.args.get('oauth_token'), session['request_token_secret'], method='POST', header_auth=True, data={'oauth_verifier': request.args.get('oauth_verifier')})

    session['obp_token'] = access_token
    session['obp_token_secret'] = access_token_secret

    return redirect("/payment")

@app.route("/payment", methods=['GET', 'POST'])
def payment():
    obp_session = CONNECTED_BANKS[session.get('bank_name', 'sandbox')]['service'].get_session(token=(session.get('obp_token', 'HOI3HARUUJ2435VQEM4PF2SZ4BVTVMZR0ULDIDYY'), session.get('obp_token_secret', 'RVG5Q0KCUD3FMHAUXOHT5IBQAOYGSLRQVIE2MLIC')))

    if request.method == 'POST':
        account_id, bank_id = request.form['account_select'].split("|")
        response = obp_session.post('banks/%s/accounts/%s/owner/transactions' % (bank_id, account_id),
                                    data=json.dumps({'account_id': MERCHANT_ACCOUNT_ID, 'bank_id': MERCHANT_BANK_ID, 'amount': AMOUNT}),
                                    header_auth=True,
                                    headers={'Content-Type': 'application/json'})
        transaction = response.json()

        flash("Sucessfully submitted wire: %s" % transaction['transaction_id'])

        return redirect('/')
    else:
        accounts = obp_session.get('accounts', header_auth=True)
        parsed_accounts = accounts.json()
        usable_accounts = [account for account in parsed_accounts.get('accounts', []) if any([view.get('id', '') == 'owner' for view in account.get('views_available', [])])]
        account_details = [obp_session.get('banks/%s/accounts/%s/owner/account' % (account['bank_id'], account['id']), header_auth=True).json() for account in usable_accounts]

        return render_template('payment.html', accounts=account_details, amount=AMOUNT)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app.run(port=3000, debug=True)
