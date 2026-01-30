// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IGaiaVault {
    event Deposited(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);
    event YieldDistributed(address indexed charity, uint256 amount);

    /**
     * @dev Deposit tokens into the vault.
     */
    function deposit(uint256 amount) external;

    /**
     * @dev Withdraw principal from the vault (primarily for No-Loss).
     */
    function withdraw(uint256 amount) external;

    /**
     * @dev Distribute the accrued yield to the charity (primarily for No-Loss).
     */
    function distributeYield() external;

    /**
     * @dev Returns the underlying asset of the vault.
     */
    function asset() external view returns (IERC20);

    /**
     * @dev Returns the charity address the vault is supporting.
     */
    function charity() external view returns (address);
}
