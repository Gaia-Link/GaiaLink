// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {IDeFiStrategy} from "../interfaces/IDeFiStrategy.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title MockAaveStrategy
 * @dev Simulates a yield-generating strategy (e.g., Aave Landing Pool).
 * Yield is simulated by manually sending tokens to this contract via `simulateYield`.
 */
contract MockAaveStrategy is IDeFiStrategy, Ownable {
    using SafeERC20 for IERC20;

    IERC20 public immutable assetToken;
    uint256 public depositedPrincipal;

    constructor(address _asset, address _owner) Ownable(_owner) {
        assetToken = IERC20(_asset);
    }

    function asset() external view returns (address) {
        return address(assetToken);
    }

    /**
     * @dev Deposits funds into the strategy.
     */
    function deposit(uint256 amount) external {
        assetToken.safeTransferFrom(msg.sender, address(this), amount);
        depositedPrincipal += amount;
    }

    /**
     * @dev Withdraws principal from the strategy.
     * Only owner (Vault) can withdraw.
     */
    function withdraw(uint256 amount) external onlyOwner {
        require(depositedPrincipal >= amount, "Insufficient principal");
        depositedPrincipal -= amount;
        assetToken.safeTransfer(msg.sender, amount);
    }

    /**
     * @dev Returns total assets held (Principal + Yield).
     */
    function totalAssets() external view returns (uint256) {
        return assetToken.balanceOf(address(this));
    }

    /**
     * @dev Harvests yield (Total - Principal) and sends to Valut.
     * Only owner (Vault) can harvest.
     */
    function harvest() external onlyOwner returns (uint256 yield) {
        uint256 total = assetToken.balanceOf(address(this));
        if (total > depositedPrincipal) {
            yield = total - depositedPrincipal;
            assetToken.safeTransfer(msg.sender, yield);
        }
    }
    
    /**
     * @dev Helper to simulate yield. Any user can "donate" interest to the strategy.
     */
    function simulateYield(uint256 amount) external {
        assetToken.safeTransferFrom(msg.sender, address(this), amount);
    }
}
