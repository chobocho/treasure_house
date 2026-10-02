// 슬라이드 p8-v7-tuple-mutable — 고칠 수 있는 구조체, C# 7.0
using System;
using System.Collections.Generic;

class App
{
    static void Main()
    {
        var a = (x: 1, y: 2);
        var b = a;                  // a copy: tuples are structs
        b.x = 10;
        Console.WriteLine(a + " " + b);

        var arr = new[] { (x: 1, y: 2) };
        arr[0].x = 5;               // array element: a variable
        Console.WriteLine(arr[0]);

        var list = new List<(int x, int y)> { (1, 2) };
        var item = list[0];         // indexer returns a copy
        item.x = 5;
        Console.WriteLine(list[0] + " " + item);
#if BAD
        list[0].x = 5;              // modifying a temporary copy
#endif
    }
}
