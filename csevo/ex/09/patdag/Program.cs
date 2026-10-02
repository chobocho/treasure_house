// 슬라이드 p9-v8-pat-dag — 검사를 나눠 쓰는 결정 DAG, C# 8.0
using System;

class Box
{
    public static int Reads;
    int kind, size;
    public Box(int k, int s) { kind = k; size = s; }
    public int Kind { get { Reads++; return kind; } }
    public int Size { get { Reads++; return size; } }
}

class App
{
    // Kind appears in five arms; how often is it read?
    static string Label(Box b) => b switch
    {
        { Kind: 1, Size: 1 } => "small one",
        { Kind: 1, Size: 2 } => "medium one",
        { Kind: 1 } => "big one",
        { Kind: 2, Size: 1 } => "small two",
        { Kind: 2 } => "two",
        _ => "other",
    };

    static void Main()
    {
        var boxes = new[]
        {
            new Box(1, 1), new Box(1, 3), new Box(2, 9), new Box(5, 1),
        };
        foreach (Box b in boxes)
        {
            Box.Reads = 0;
            string s = Label(b);
            Console.WriteLine("{0,-10} getter calls: {1}",
                s, Box.Reads);
        }
    }
}
