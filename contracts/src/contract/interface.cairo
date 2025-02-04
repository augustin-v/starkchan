#[starknet::interface]
pub trait IHelloStarkChan<TContractState> {
    fn get_id(self: @TContractState) -> usize;
    fn poseidon_hash(ref self: TContractState, id: usize, cup_size: u8) -> felt252;
    fn verify_cup_size_with_cup(ref self: TContractState, input: u8);
    fn verify_cup_size_with_hash(ref self: TContractState, input: felt252);
    fn is_winner(ref self: TContractState) -> bool;
}