# Aurolab Voice Order Assistant

A local web app that:
1. Captures speech in the browser and converts it to text.
2. Matches product names against the supplied `products.csv`.
3. Extracts quantities and combines repeated product lines.
4. Shows an editable order table.
5. Opens a normal Gmail compose window with the reviewed order.

## Requirements
- Windows 10/11
- Python 3.10 or newer
- Google Chrome recommended
- Internet connection for initial package installation; speech recognition may use the browser's online speech service.

## Run on Windows

1. Extract `Aurolab_Voice_Order_Assistant.zip`.
2. Open the extracted `aurolab_voice_ordering` folder.
3. Click the folder address bar, type `cmd`, and press Enter.
4. Run:

   ```bat
   py -m venv venv
   venv\Scripts\activate
   py -m pip install -r requirements.txt
   py app.py
   ```

   If `py` is not recognised, use `python` instead.

5. Open Google Chrome and visit:

   `http://127.0.0.1:5000`

6. Allow microphone permission when Chrome asks.

## How to use
- Click **Start recording**, speak product names and quantities, then click **Stop recording**.
- You can also type or correct the transcript manually.
- Click **Match products**.
- Review product names and quantities in the table. Edit, remove, or add products as needed.
- Click **Prepare Gmail order**. Gmail opens with the subject and order details filled in. Enter the recipient and click Send yourself.

## Example speech
"Auroflex ten pieces, Aurovue five pieces."

The quantity can be spoken as a number or common number word. Say the product name first and its quantity immediately after it for best results.

## About the supplied CSV
The supplied file has four columns:
- `IOL`: category
- `Aurolens`: product name
- `Aurolene`: alternate product-name spelling/alias
- `a089B000000wNFhQAM`: record identifier

The app uses the two product-name columns for matching and does not show record IDs in the order email. Rows containing `test` are ignored.

## Important notes and limitations
- Use Chrome on localhost for microphone access. The browser's built-in Web Speech API is used; this is not a custom-trained speech model, and recognition quality depends on microphone quality, accent, background noise and browser support.
- Product matching is based on the supplied catalogue and conservative fuzzy text matching. Always review similar product names before preparing an email.
- If a product is not recognised, add it manually or correct the transcript.
- Gmail opens in a browser tab. The app does not send email automatically and does not need Gmail API credentials.
- This starter version is designed for one spoken order at a time. Review the quantity for every line before sending.
- Keep `products.csv` in the same folder as `app.py`.
