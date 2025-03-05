# Project API Documentation

## Available APIs:

### 1. **POST /auth/register/**
   - **Description**: Register a new user.
   
### 2. **POST /auth/login/**
   - **Description**: Login with existing user credentials.

### 3. **GET /api/events**
   - **Description**: Retrieve all events.

### 4. **POST /api/events**
   - **Description**: Create a new event.

### 5. **PATCH /api/events**
   - **Description**: Update an existing event.

### 6. **DELETE /api/events**
   - **Description**: Delete an event.

### 7. **POST /api/orders/reserve/**
   - **Description**: Reserve tickets for events.

### 8. **POST /api/orders/{order_id}/purchase/**
   - **Description**: Complete the purchase for an order.

### 9. **GET /api/tickets/**
   - **Description**: Get all tickets for the user.

### 10. **GET /api/orders/**
   - **Description**: Get all orders for the user.

### 11. **DELETE /api/orders/{order_id}/cancel/**
   - **Description**: Cancel a specific order.

### 12. **GET /api/payments/**
   - **Description**: Return True or False.
