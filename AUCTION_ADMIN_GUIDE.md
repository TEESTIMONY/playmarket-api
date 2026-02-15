# Auction System Admin Guide

## Overview

This guide provides complete instructions for managing the PlayMarket auction system through Django admin interface.

## Django Admin Access

### Login Credentials
- **URL**: `http://127.0.0.1:8000/admin/`
- **Username**: `delo`
- **Password**: *Your chosen password*

## Auction Management

### Creating an Auction

1. **Via Django Admin:**
   - Navigate to: `Admin Dashboard` → `Bounties` → `Auctions` → `Add Auction`
   - Fill in the auction details:
     - **Title**: Name of the auction item
     - **Description**: Detailed description
     - **Minimum Bid**: Starting bid amount
     - **Starts At**: When auction becomes active
     - **Ends At**: When auction closes
     - **Created By**: Admin user (auto-filled)

2. **Via Management Command:**
   ```bash
   # Create a new auction
   python3 manage.py create_single_auction --title "iPhone 15 Pro" --minimum-bid 1000 --duration 24
   
   # Create auction that starts immediately
   python3 manage.py create_single_auction --starts-in 0 --duration 12
   ```

### Single Auction Constraint

The system enforces that only **one auction can be active at a time**:

- **Status States**: `pending` → `active` → `ended`
- **Validation**: API prevents creating new auctions when one is active
- **Admin Control**: Use bulk actions to manage auction status

### Managing Auction Status

In Django admin, use the bulk actions:

1. **Activate Auctions**: Change status from `pending` to `active`
2. **Deactivate Auctions**: Change status from `active` to `pending`
3. **End Auctions**: Determine winners and close auction

### Auction Fields in Admin

- **Title**: Auction item name
- **Minimum Bid**: Starting bid amount
- **Current Highest Bid**: Live highest bid amount
- **Current Highest Bidder**: User with highest bid
- **Total Bids**: Number of bids placed
- **Status**: Current auction state
- **Starts At**: When auction becomes active
- **Ends At**: When auction closes
- **Created By**: Admin who created the auction

## User Management

### User Overview

Access detailed user information:
- **URL**: `Admin Dashboard` → `Authentication and Authorization` → `Users` → Select User → `View User Overview`

### User Statistics

- **Coin Balance**: Current coin amount
- **Total Earned**: Coins from bounties
- **Total Redeemed**: Coins from redeem codes
- **Net Balance**: Current balance
- **Bounty Claims**: List of claimed bounties
- **Recent Transactions**: Last 10 coin transactions
- **Used Redeem Codes**: Redeemed codes history

### Managing User Coins

- **View Balance**: In user profile
- **Add Coins**: Create manual transactions
- **Deduct Coins**: For auction payments or penalties

## Bid Management

### Viewing Bids

- **URL**: `Admin Dashboard` → `Bounties` → `Auction Bids`
- **Filter**: By auction, user, or date
- **Sort**: By bid amount or creation date

### Bid Status

- **Pending**: Bid under review
- **Accepted**: Valid and active bid
- **Rejected**: Bid was rejected
- **Outbid**: Surpassed by higher bid
- **Cancelled**: Bid was cancelled

## Winner Management

### Viewing Winners

- **URL**: `Admin Dashboard` → `Bounties` → `Auction Winners`
- **Information**: Winner details, winning amount, transfer status

### Transfer Management

- **Coins Transferred**: Whether payment was completed
- **Transfer Date**: When transfer was completed
- **Manual Transfer**: Complete transfers if needed

## Bulk Operations

### Auction Actions

1. **Select Multiple Auctions**
2. **Choose Action**:
   - Activate selected pending auctions
   - Deactivate selected active auctions
   - End selected active auctions and determine winners

### User Actions

1. **Select Multiple Users**
2. **Choose Action**:
   - View user overview
   - Export user data

## Monitoring and Analytics

### Real-time Data

- **Current Highest Bids**: Live updates in admin
- **Bid Counts**: Real-time bid statistics
- **Auction Status**: Live status updates

### Audit Trail

- **Transaction History**: Complete coin transaction log
- **Bid History**: All bid attempts and outcomes
- **User Activity**: User actions and changes

## Troubleshooting

### Common Issues

1. **"Active auction already exists"**
   - Use `--force` flag with management command
   - Or deactivate existing auction first

2. **"Insufficient coin balance"**
   - Check user's coin balance in admin
   - Add coins manually if needed

3. **"Auction not accepting bids"**
   - Check auction status is `active`
   - Verify auction timing (starts_at, ends_at)

### Error Resolution

- **Check Logs**: Django admin shows error messages
- **Validate Data**: Ensure all required fields are filled
- **Check Permissions**: Verify admin user has proper permissions

## Best Practices

### Auction Creation

1. **Set Realistic Minimum Bids**: Based on item value
2. **Proper Timing**: Allow sufficient bidding time
3. **Clear Descriptions**: Detailed item information
4. **Monitor Activity**: Watch for suspicious bidding

### User Management

1. **Regular Monitoring**: Check for unusual activity
2. **Coin Management**: Handle disputes fairly
3. **Communication**: Keep users informed of status changes

### Security

1. **Admin Access**: Limit admin user creation
2. **Audit Logs**: Monitor all admin actions
3. **Data Backup**: Regular database backups

## API Integration

### Admin API Endpoints

- **Create Auction**: `POST /api/auctions/create/`
- **List Auctions**: `GET /api/auctions/`
- **Place Bid**: `POST /api/auctions/{id}/bid/`
- **End Auction**: `POST /api/auctions/{id}/end/`

### Authentication

- **Admin Token**: Required for admin operations
- **User Token**: Required for user operations
- **Validation**: All requests validated for permissions

## Support

For additional support:
- Check Django admin logs
- Review API documentation
- Monitor system performance
- Contact development team for technical issues