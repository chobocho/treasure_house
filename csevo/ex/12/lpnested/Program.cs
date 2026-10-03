// 슬라이드 p12-v11-lp-nested — 겹친 목록 패턴과 속성 패턴, C# 11
using System;

record Order(string Id, int[] Qty);

class Program
{
    static string Check(Order o) => o switch
    {
        { Qty: [] } => "no lines",
        { Id: ['A', ..], Qty: [> 0, ..] } => "A-order",
        { Qty: [.., > 100] } => "big last line",
        { Qty.Length: > 3 } => "long",
        _ => "plain",
    };

    static void Main()
    {
        Console.WriteLine(Check(new Order("B1", new int[0])));
        Console.WriteLine(Check(new Order("A7", new[] { 2, 500 })));
        Console.WriteLine(Check(new Order("B2", new[] { 2, 500 })));
        Console.WriteLine(Check(new Order("B3", new[] { 1, 1, 1, 1 })));
        Console.WriteLine(Check(new Order("A8", new[] { 0, 1 })));

        int[][] grid = { new[] { 1, 0 }, new[] { 5 }, new[] { 0, 9 } };
        Console.WriteLine(grid is [[1, ..], .., [.., 9]]);
        Console.WriteLine(grid is [_, [var only], _] ? only : -1);

        int[] a = { 1, 2, 3, 4 };
        Console.WriteLine(a is [1, .. [2, 3], 4]);
        Console.WriteLine(a is [1, .. { Length: 2 }, _]);
    }
}
