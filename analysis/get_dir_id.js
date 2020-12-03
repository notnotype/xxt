ul = document.querySelectorAll('.con')
for (let li in ul.children) {
    if (ul.children.hasOwnProperty(li)) {
        li = ul.children[li];
        console.log(li.getAttribute('id') + '\n')
    }
}

// 68773828
// 68773829
// 68773832
// 68773852
// 68773853
// 68773855
// 68773856

[68773828,
68773829,
68773832,
68773852,
68773853,
68773855,
68773856]