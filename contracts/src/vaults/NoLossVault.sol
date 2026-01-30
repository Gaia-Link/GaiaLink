// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {IGaiaVault} from "../interfaces/IGaiaVault.sol";
import {IDeFiStrategy} from "../interfaces/IDeFiStrategy.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title NoLossVault
 * @dev No-Loss donation vault that routes funds to a DeFi Strategy.
 * Implements Yield Splitting: Platform Fee vs Charity Donation.
 */
contract NoLossVault is IGaiaVault, Ownable {
    using SafeERC20 for IERC20;

    IERC20 public immutable underlying;
    address public immutable charityAddress;
    address public immutable platformAddress;
    
    IDeFiStrategy public strategy;
    
    // Fee Config: 5% (500 bps)
    uint256 public constant PLATFORM_FEE_BPS = 500;
    uint256 public constant MAX_BPS = 10000;

    mapping(address => uint256) public userPrincipal;
    uint256 public totalPrincipal;

    constructor(
        IERC20 _underlying, 
        address _charity, 
        address _owner, 
        address _platform,
        address _strategy
    ) Ownable(_owner) {
        underlying = _underlying;
        charityAddress = _charity;
        platformAddress = _platform;
        strategy = IDeFiStrategy(_strategy);
    }

    function deposit(uint256 amount) external override {
        underlying.safeTransferFrom(msg.sender, address(this), amount);
        
        // Push to Strategy
        underlying.approve(address(strategy), amount);
        strategy.deposit(amount);

        userPrincipal[msg.sender] += amount;
        totalPrincipal += amount;
        emit Deposited(msg.sender, amount);
    }

    function withdraw(uint256 amount) external override {
        require(userPrincipal[msg.sender] >= amount, "Insufficient principal");
        
        // Pull from Strategy
        strategy.withdraw(amount);
        
        userPrincipal[msg.sender] -= amount;
        totalPrincipal -= amount;
        
        underlying.safeTransfer(msg.sender, amount);
        emit Withdrawn(msg.sender, amount);
    }

    /**
     * @dev Harvests yield from strategy and splits it.
     */
    function distributeYield() external override {
        // 1. Harvest from Strategy
        uint256 yieldAmount = strategy.harvest();
        
        if (yieldAmount > 0) {
            // 2. Calculate Split
            uint256 fee = (yieldAmount * PLATFORM_FEE_BPS) / MAX_BPS;
            uint256 charityShare = yieldAmount - fee;

            // 3. Distribute
            if (fee > 0) {
                underlying.safeTransfer(platformAddress, fee);
            }
            if (charityShare > 0) {
                underlying.safeTransfer(charityAddress, charityShare);
                emit YieldDistributed(charityAddress, charityShare);
            }
        }
    }

    function asset() external view override returns (IERC20) {
        return underlying;
    }

    function charity() external view override returns (address) {
        return charityAddress;
    }
}
