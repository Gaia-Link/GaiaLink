// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IDeFiStrategy {
    function asset() external view returns (address);
    function deposit(uint256 amount) external;
    function withdraw(uint256 amount) external;
    
    // Returns the total value managed by the strategy (Principal + Yield)
    function totalAssets() external view returns (uint256);
    
    // Harvests accrued yield and sends it to the Vault
    function harvest() external returns (uint256);
}
