use snforge_std::DeclareResultTrait;
use snforge_std::{declare, ContractClassTrait, start_cheat_caller_address};
use contracts::contract::interface::{IHelloStarkChanDispatcher,IHelloStarkChanDispatcherTrait};
use starknet::ContractAddress;
use core::poseidon::PoseidonTrait;
use core::hash::{HashStateTrait, HashStateExTrait};

// Replicate contract's hash structure in test
#[derive(Drop, Hash)]
struct TestHashStruct {
    first: usize,
    second: u8
}
fn deploy_contract() -> ContractAddress {
    let contract = declare("HelloStarkChan").unwrap().contract_class();
    let (address, _) = contract.deploy(@array![]).unwrap();
    address
}

#[test]
fn test_constructor() {
    let address = deploy_contract();
    let dispatcher = IHelloStarkChanDispatcher { contract_address: address };
    assert!(dispatcher.get_id() == 4649, "ID mismatch");
}

#[test]
fn test_valid_cup_guess() {
    let address = deploy_contract();
    let dispatcher = IHelloStarkChanDispatcher { contract_address: address };
    
    // Get correct hash through contract function
    let correct_hash = dispatcher.get_cup_hash();
    let caller: ContractAddress = 123.try_into().unwrap();
    
    start_cheat_caller_address(address, caller);
    dispatcher.verify_cup_size_with_hash(correct_hash);
    assert!(dispatcher.is_winner(), "Should be winner after correct hash guess");
}

#[test]
#[should_panic(expected: "Wrong input")]
fn test_invalid_cup_guess() {
    let address = deploy_contract();
    let dispatcher = IHelloStarkChanDispatcher { contract_address: address };
    dispatcher.verify_cup_size_with_cup(9); // Below valid range
}

#[test]
fn test_hash_verification() {
    let address = deploy_contract();
    let dispatcher = IHelloStarkChanDispatcher { contract_address: address };
    
    // Generate valid hash for verification
    let correct_hash = dispatcher.get_cup_hash();
    dispatcher.verify_cup_size_with_hash(correct_hash);
    assert!(dispatcher.is_winner(), "Caller should be marked as winner");
}

#[test]
#[should_panic(expected: "Wrong input")]
fn test_invalid_hash() {
    let address = deploy_contract();
    let dispatcher = IHelloStarkChanDispatcher { contract_address: address };
    dispatcher.verify_cup_size_with_hash(12345.try_into().unwrap());
}

#[test]
fn test_randomization_range() {


    let contract_address = deploy_contract();
    let dispatcher = IHelloStarkChanDispatcher { contract_address };
    let cup_hash = dispatcher.get_cup_hash();

    let mut valid_count = 0;
    let mut cup_size: u8 = 10;
    
    // Cairo-compatible while loop
    while cup_size <= 15 {
        let hash_struct = TestHashStruct {
            first: 4649,
            second: cup_size
        };
        
        let test_hash = PoseidonTrait::new();

        let test_hash = test_hash            
            .update_with(hash_struct)
            .finalize();
        if test_hash == cup_hash {
            valid_count += 1;
        }
        
        cup_size += 1;
    };
    
    assert!(valid_count == 1, "Should have exactly one valid cup size");
}