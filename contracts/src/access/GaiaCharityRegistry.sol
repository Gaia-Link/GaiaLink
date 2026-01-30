// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title GaiaCharityRegistry
 * @dev 2-Tier governance registry for humanitarian organizations.
 * Tier 1: Platform Owner (vets charities)
 * Tier 2: Charity Admin (manages own members)
 */
contract GaiaCharityRegistry is Ownable {
    
    struct Charity {
        string name;
        address admin;
        bool isActive;
        mapping(address => bool) members;
    }

    // Maps charity ID to Charity struct
    mapping(uint256 => Charity) public info;
    mapping(address => uint256) public adminToCharityId;
    
    uint256 public nextCharityId = 1;

    event CharityRegistered(uint256 indexed charityId, string name, address indexed admin);
    event MemberAdded(uint256 indexed charityId, address indexed member);
    event MemberRemoved(uint256 indexed charityId, address indexed member);

    constructor(address _owner) Ownable(_owner) {}

    /**
     * @dev Tier 1: Register a new verified charity.
     */
    function registerCharity(address _admin, string calldata _name) external onlyOwner {
        require(_admin != address(0), "Invalid admin");
        require(adminToCharityId[_admin] == 0, "Admin already manages a charity");

        uint256 id = nextCharityId++;
        Charity storage c = info[id];
        c.name = _name;
        c.admin = _admin;
        c.isActive = true;
        
        // Admin is automatically a member
        c.members[_admin] = true;
        adminToCharityId[_admin] = id;

        emit CharityRegistered(id, _name, _admin);
    }

    /**
     * @dev Tier 2: Charity Admin adds operational members.
     */
    function addMember(address _member) external {
        uint256 id = adminToCharityId[msg.sender];
        require(id != 0, "Not a charity admin");
        
        info[id].members[_member] = true;
        emit MemberAdded(id, _member);
    }

    /**
     * @dev Tier 2: Charity Admin removes operational members.
     */
    function removeMember(address _member) external {
        uint256 id = adminToCharityId[msg.sender];
        require(id != 0, "Not a charity admin");
        require(_member != info[id].admin, "Cannot remove admin");

        info[id].members[_member] = false;
        emit MemberRemoved(id, _member);
    }

    /**
     * @dev Check if an address is an authorized member of a specific charity.
     */
    function isMember(uint256 _charityId, address _account) external view returns (bool) {
        return info[_charityId].isActive && info[_charityId].members[_account];
    }
    
    /**
     * @dev Get charity details by ID (excluding members mapping).
     */
    function getCharity(uint256 _charityId) external view returns (string memory name, address admin, bool isActive) {
        Charity storage c = info[_charityId];
        return (c.name, c.admin, c.isActive);
    }
}
