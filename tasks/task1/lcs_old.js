// collect args
const args = process.argv.slice(2);

// deduce shortest word index
const find_idx_of_smallest = (arr) => {
    let smallest = 0;
    for (let i = 0; i < arr.length; i++) {
        if (arr[i] < arr[smallest]) smallest = i;
    }
    return smallest;
};

const idx_of_shortest = find_idx_of_smallest(args.map((str) => str.length));
const shortest_word = args[idx_of_shortest];

// structure shortest word
args.splice(idx_of_shortest, 1);

let starting_indices = [];
for (let char_idx = 0; char_idx < shortest_word.length; char_idx++) {
    starting_indices.push(
        args.map((str) => {
            let indices = [];
            for (let str_char_idx = 0; str_char_idx < str.length; str_char_idx++
            ) {
                if (str[str_char_idx] == shortest_word[char_idx]) {
                    indices.push(str_char_idx);
                }
            }
            return indices;
        }),
    );
}

for(let word_idx = 0; word_idx < args.length; word_idx++){
    
}

console.log(starting_indices);
