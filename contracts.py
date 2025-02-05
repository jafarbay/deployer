import random

contracts = [
    {
        "name": "AdvancedStorage",
        "source": """
        pragma solidity ^0.8.0;
        contract AdvancedStorage {
            uint256 private value;
            event ValueChanged(uint256 newValue);
            
            constructor(uint256 _value) {
                value = _value;
            }
            
            function setValue(uint256 _value) public {
                value = _value;
                emit ValueChanged(_value);
            }
            
            function getValue() public view returns (uint256) {
                return value;
            }
        }
        """,
        "constructor_args_generator": lambda: [random.randint(1, 5)]
    },
    {
        "name": "Voting",
        "source": """
        pragma solidity ^0.8.0;
        contract Voting {
            mapping(string => uint256) public votes;
            event Voted(string option, uint256 votes);
            
            function vote(string memory _option) public {
                votes[_option]++;
                emit Voted(_option, votes[_option]);
            }
        }
        """,
        "constructor_args_generator": lambda: []  # Нет конструктора, поэтому пустой список
    },
    {
        "name": "Lottery",
        "source": """
        pragma solidity ^0.8.0;
        contract Lottery {
            address[] public players;
            address public winner;
            
            function enter() public payable {
                require(msg.value > 0.01 ether, "Minimum ETH required");
                players.push(msg.sender);
            }
            
            function pickWinner() public {
                require(players.length > 0, "No players yet");
                uint index = uint(keccak256(abi.encodePacked(block.timestamp, msg.sender))) % players.length;
                winner = players[index];
                payable(winner).transfer(address(this).balance);
            }
        }
        """,
        "constructor_args_generator": lambda: []  # Нет конструктора, пустой список
    }
]

def get_random_contract():
    """Возвращает случайный контракт с рандомными аргументами конструктора"""
    contract = random.choice(contracts)
    constructor_args = contract["constructor_args_generator"]()
    return contract["name"], contract["source"], constructor_args
