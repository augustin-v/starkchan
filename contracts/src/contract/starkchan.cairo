#[starknet::contract]
mod HelloStarkChan {
    use starknet::storage::StoragePathEntry;
    use contracts::contract::interface::IHelloStarkChan;
    use core::starknet::storage::{StoragePointerReadAccess, StoragePointerWriteAccess, Map};
    use core::poseidon::PoseidonTrait;
    use core::starknet::{get_block_timestamp, get_block_number, get_contract_address, ContractAddress, get_caller_address};
    use core::hash::{HashStateTrait, HashStateExTrait};

    #[storage]
    struct Storage {
        cup_hash: felt252,
        id: usize,
        winners: Map<ContractAddress, bool>,
    }

    #[derive(Drop, Hash)]
    struct HashStruct {
        first: usize, // id
        second: u8 // cup size
    }

    // for pseudo random seed
    #[derive(Drop, Hash)]
    struct HashStruct2 {
        first: u64, 
        second: u64,
        third: felt252,
    }

    #[constructor]
    fn constructor(ref self: ContractState) {
        let cup_size = self._get_pseudo_random(10, 15); // Maps to cup sizes A-F
        self.id.write(4649);
    
        let hash_struct = HashStruct { 
            first: self.id.read(), 
            second: cup_size 
        };
        let hash = PoseidonTrait::new()
            .update_with(hash_struct)
            .finalize();
        
        self.cup_hash.write(hash);
    }

    

    #[abi(embed_v0)]
    impl HelloStarkChanImpl of IHelloStarkChan<ContractState> {
        fn get_id(self: @ContractState) -> usize {
            self.id.read()
        }
        fn poseidon_hash(ref self: ContractState, id: usize, cup_size: u8) -> felt252 {
            let input = HashStruct { first: id, second: cup_size };
            PoseidonTrait::new().update_with(input).finalize()
        }
        

        fn verify_cup_size_with_cup(ref self: ContractState, input: u8) {
            
            let hash_struct = HashStruct { first: 4649, second: input };
            let hash = PoseidonTrait::new();
            let hash = hash.update_with(hash_struct).finalize();
            
            assert!(hash == self.cup_hash.read(), "Wrong input");
            
            let caller = get_caller_address();
            self.winners.entry(caller).write(true);
        }

        // user needs to generate a poseidon hash with the supposed cup hash (from 10 to 15 (A-F)) and the AI id
        fn verify_cup_size_with_hash(ref self: ContractState, input: felt252) {
            assert!(input == self.cup_hash.read(), "Wrong input");

            let caller = get_caller_address();
            self.winners.entry(caller).write(true);
        }

    fn is_winner(ref self: ContractState) -> bool {
        self.winners.entry(get_caller_address()).read()
    }

    }

        #[generate_trait]
    impl Private of PrivateTrait {
        fn _get_pseudo_random(ref self: ContractState, min: u8, max: u8) -> u8 {

            let hash = PoseidonTrait::new();
            let tmp = HashStruct2 { 
                first: get_block_timestamp(),
                second: get_block_number(),
                third: get_contract_address().into()

            };

            let seed: u256 = hash.update_with(tmp).finalize().into();

            // (15-10+1=6 possible values)
            ((seed % (max.into() - min.into() + 1)) + min.into()).try_into().unwrap()
        }
    }
}