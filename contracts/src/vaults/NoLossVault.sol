// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {IGaiaVault} from "../interfaces/IGaiaVault.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title NoLossVault
 * @dev Simple simulation of a No-Loss vault. Yield is simulated/donated.
 * In production, this would deposit into Euler/Pendle.
 */
contract NoLossVault is IGaiaVault, Ownable {
    using SafeERC20 for IERC20;

    IERC20 public immutable underlying;
    address public immutable charityAddress;
    
    mapping(address => uint256) public userPrincipal;
    uint256 public totalPrincipal;

    constructor(IERC20 _underlying, address _charity, address _owner) Ownable(_owner) {
        underlying = _underlying;
        charityAddress = _charity;
    }

    function deposit(uint256 amount) external override {
        underlying.safeTransferFrom(msg.sender, address(this), amount);
        userPrincipal[msg.sender] += amount;
        totalPrincipal += amount;
        emit Deposited(msg.sender, amount);
    }

    function withdraw(uint256 amount) external override {
        require(userPrincipal[msg.sender] >= amount, "Insufficient principal");
        userPrincipal[msg.sender] -= amount;
        totalPrincipal -= amount;
        underlying.safeTransfer(msg.sender, amount);
        emit Withdrawn(msg.sender, amount);
    }

    /**
     * @dev Distribute yield. In this mock, we assume yield is already in the contract 
     * (e.g. sent by a yield source or donated).
     */
    function distributeYield() external override {
        uint256 balance = underlying.balanceOf(address(this));
        if (balance > totalPrincipal) {
            uint256 yieldAmount = balance - totalPrincipal;
            underlying.safeTransfer(charityAddress, yieldAmount);
            emit YieldDistributed(charityAddress, yieldAmount);
        }
    }

    function asset() external view override returns (IERC20) {
        return underlying;
    }

    function charity() external view override returns (address) {
        return charityAddress;
    }
}
