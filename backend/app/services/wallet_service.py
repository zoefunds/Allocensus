import json
from eth_account import Account
from mnemonic import Mnemonic
from app.utils.security import encrypt_private_key
from app.models.wallet import Wallet, EncryptedKeystore
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

Account.enable_unaudited_hdwallet_features()
mnemo = Mnemonic("english")


async def create_wallet_for_user(user: User, hashed_password: str, db: AsyncSession, plain_password: str | None = None) -> Wallet:
    """Generate HD wallet, store as Web3 V3 keystore JSON (browser-decryptable), persist wallet + keystore."""
    mnemonic_phrase = mnemo.generate(strength=128)
    account = Account.from_mnemonic(mnemonic_phrase, account_path="m/44'/60'/0'/0/0")

    wallet = Wallet(
        user_id=user.id,
        address=account.address,
        derivation_path="m/44'/60'/0'/0/0",
        chain_id=61999,
    )
    db.add(wallet)
    await db.flush()

    # Store as standard Web3 V3 keystore so ethers.js can decrypt client-side.
    # Falls back to AES-GCM if plain password not provided (legacy path).
    if plain_password:
        keystore_dict = Account.encrypt(account.key.hex(), plain_password)
        encrypted_pk = json.dumps(keystore_dict)
    else:
        encrypted_pk = encrypt_private_key(account.key.hex(), hashed_password)

    encrypted_mn = encrypt_private_key(mnemonic_phrase, hashed_password)

    keystore = EncryptedKeystore(
        wallet_id=wallet.id,
        encrypted_private_key=encrypted_pk,
        encrypted_mnemonic=encrypted_mn,
    )
    db.add(keystore)
    return wallet


async def export_private_key(wallet: Wallet, password: str, hashed_password: str) -> str:
    """Decrypt and return private key hex — requires valid password verification."""
    if not wallet.keystore:
        raise ValueError("No keystore found for this wallet")
    return decrypt_private_key(wallet.keystore.encrypted_private_key, hashed_password)


async def get_signer_account(wallet: Wallet, hashed_password: str) -> object:
    """Return eth_account Account object for signing Genlayer transactions."""
    pk_hex = decrypt_private_key(wallet.keystore.encrypted_private_key, hashed_password)
    return Account.from_key(pk_hex)
