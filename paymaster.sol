// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";
import {ECDSA} from "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import {EIP712} from "@openzeppelin/contracts/utils/cryptography/EIP712.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

contract GaslessPay is Ownable, ReentrancyGuard, EIP712 {
    bytes32 private constant TRANSFER_PERMIT_TYPEHASH =
        keccak256("Permit(address recipient,uint256 amount,uint256 fee)");

    mapping(address => uint256) public nonces;

    // event Transaction(address indexed sender, address indexed recipient, uint amount);
    event Transaction(
        address indexed sender,
        address indexed recipient,
        uint256 amount,
        uint256 fee,
        uint256 nonce
    );

    using SafeERC20 for IERC20;

    IERC20 public immutable token;

    constructor(IERC20 _token)
        EIP712(string.concat("GaslessPay-", ERC20(address(_token)).name()), "1")
    {
        token = _token;
    }

    function transferGasless(
        address recipient,
        uint256 amount,
        uint256 fee,
        uint256 deadline,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external nonReentrant {
        require(block.timestamp <= deadline, "GaslessPay: expired deadline");

        uint256 nonce = nonces[_msgSender()]++;
        bytes32 structHash =
            keccak256(
                abi.encode(
                    TRANSFER_WITH_SIG_TYPEHASH,
                    _msgSender(),
                    recipient,
                    amount,
                    fee,
                    nonce,
                    deadline
                )
            );
        bytes32 hash = _hashTypedDataV4(structHash);
        address signer = ECDSA.recover(hash, v, r, s);

        // Ensure the sender has enough balance to cover both the amount and the fee
        uint256 total = amount + fee;
        require(
            token.balanceOf(signer) >= total,
            "GaslessPay: insufficient balance"
        );

        // Transfer the amount to the recipient
        token.safeTransferFrom(signer, recipient, amount);

        // Compensate the relayer (the caller of this function) with the fee
        if (fee > 0) {
            token.safeTransferFrom(signer, _msgSender(), fee);
        }

        emit Transaction(signer, recipient, amount, fee, nonce);
    }
}
