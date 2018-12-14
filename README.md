# Waive/Madisonave

This is an MVP for the Waive platform for selling small amounts of short-term advertising for our screens. It currently consists of a client for users to interact with along with a server to store records of the transactions and to upload images to an s3 bucket. The client allows users to select a number of options for their advertising and to upload an asset to show on the screen. Currently, paypal is used for payments, though payment options will likely be expanded in the future. 

#### To get started with development: 

 

 - `pip3 install -r requirements.text`
 - `npm install`
 - install sqlite3 if it is not installed
 - to create the database run `sqlite3 ad-platform.db < create-tables.sql`
 - make sure the aws cli tool is configured correctly with both an aws_access_key_id and aws_secret_access_key and that there is an s3 bucket associated with those accounts
 - `npm run sass` to start compliling the server
 - `npm start` to start the server
 - visit localhost:5050 in a browser to view the page

