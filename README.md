# MyShopWebsite

MyShopWebsite is a simple web application imitating an online store. The project is still under development and aims to provide basic e-commerce functionalities. The application currently supports:
- User registration and login.
- Adding items for sale.
- Adding items to cart.
- Viewing your added items.
- Editing details of added items.

## Features

### Currently implemented:
1. **User Registration and Login**:
   - Users can create accounts and log in using forms.
2. **Listing Items for Sale**:
   - Users can add new items for sale by specifying their name, category, price, quantity, and description.
3. **Adding items to the cart**
     - Users can add items that were added by others to the cart to later buy them (buying not implemented!).
4. **Viewing Added Items**:
   - The "My Items" page displays all items added by the user.
5. **Editing Items**:
   - Users can update details of their items (e.g., name, category, price, quantity, or description).

### In Progress:
1. **Buying Items**:
   - Adding functionality for purchasing added items by other users.

## How to Run the Application

1. Clone the repository:
   ```bash
   git clone <REPOSITORY_URL>
   cd MyShopWebsite
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Linux/Mac
   venv\Scripts\activate   # On Windows
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python run.py
   ```

5. Open your web browser and go to [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Contribution
If you would like to contribute to the project:
1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature/feature-name
   ```
3. Make your changes and submit a pull request.

