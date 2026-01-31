// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {IGaiaVault} from "../interfaces/IGaiaVault.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

contract DirectVault is IGaiaVault, Ownable {
    using SafeERC20 for IERC20;

    IERC20 public immutable underlying;
    address public immutable charityAddress;
    mapping(address => bool) public isWhitelisted;
    
    // Donation Tracking
    mapping(address => uint256) public donors;
    uint256 public totalDonated;

    constructor(IERC20 _underlying, address _charity, address _owner) Ownable(_owner) {
        underlying = _underlying;
        charityAddress = _charity;
        isWhitelisted[_charity] = true;
    }

    /**
     * @dev Deposit tokens to the vault to be held for the charity.
     */
    function deposit(uint256 amount) external override {
        underlying.safeTransferFrom(msg.sender, address(this), amount);
        donors[msg.sender] += amount;
        totalDonated += amount;
        emit Deposited(msg.sender, amount);
    }

    /**
     * @dev Withdraw funds from the vault. Only for charity or whitelisted.
     */
    function withdraw(uint256 amount) external override {
        require(msg.sender == charityAddress || isWhitelisted[msg.sender], "DirectVault: unauthorized");
        underlying.safeTransfer(msg.sender, amount);
        emit Withdrawn(msg.sender, amount);
    }

    /**
     * @dev Add an address to the withdrawal whitelist.
     */
    function addToWhitelist(address account) external onlyOwner {
        isWhitelisted[account] = true;
    }

    /**
     * @dev Distribute yield (not applicable for DirectVault).
     */
    function distributeYield() external override {
        revert("DirectVault: no yield to distribute");
    }

    function asset() external view override returns (IERC20) {
        return underlying;
    }

    function charity() external view override returns (address) {
        return charityAddress;
    }
}
