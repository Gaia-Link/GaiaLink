// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title GaiaAgentRegistry
 * @dev Manages the authorization of SpoonOS Agents within the GaiaLink ecosystem.
 */
contract GaiaAgentRegistry is Ownable {
    mapping(address => bool) public isAuthorizedAgent;

    event AgentAuthorized(address indexed agent);
    event AgentRevoked(address indexed agent);

    constructor() Ownable(msg.sender) {}

    /**
     * @dev Authorize a new agent.
     */
    function authorizeAgent(address agent) external onlyOwner {
        isAuthorizedAgent[agent] = true;
        emit AgentAuthorized(agent);
    }

    /**
     * @dev Revoke an agent's authorization.
     */
    function revokeAgent(address agent) external onlyOwner {
        isAuthorizedAgent[agent] = false;
        emit AgentRevoked(agent);
    }

    /**
     * @dev Check if an address is an authorized agent.
     */
    function isAuthorized(address agent) external view returns (bool) {
        return isAuthorizedAgent[agent];
    }
}
