// 슬라이드 p10-v9-init-indexer — init 인덱서, C# 9.0
using System;

class Row
{
    readonly string[] cells = new string[3];

    public string this[int i]
    {
        get => cells[i];
        init => cells[i] = value;            // init on an indexer
    }

    public override string ToString() => string.Join("|", cells);
}

class App
{
    static void Main()
    {
        var r = new Row { [0] = "a", [2] = "c" };   // C# 6 syntax
        Console.WriteLine(r);
#if BAD
        r[1] = "b";
#endif
    }
}
