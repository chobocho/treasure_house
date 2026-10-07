// 슬라이드 p15-sum-old — 같은 프로그램의 C# 13 판, C# 13
using System;
using System.Collections.Generic;

delegate bool Parse(string s, out int v);

static class Ext
{
    public static int Total(this ReadOnlySpan<int> s)
    {
        int t = 0;
        foreach (int x in s) t += x;
        return t;
    }
}

class Bag
{
    private string label = "";
    public string Label { get => label; set => label = value.Trim(); }
    public List<int> Items = new();
    public static Bag operator +(Bag b, int x)
    {
        var r = new Bag { Label = b.Label };
        r.Items.AddRange(b.Items);
        r.Items.Add(x);
        return r;
    }
}

class Program
{
    static void Main()
    {
        Parse p = (string s, out int v) => int.TryParse(s, out v);
        Bag bag = new Bag(), none = null;
        if (bag != null) bag.Label = "  fruit ";
        if (none != null) none.Label = "x";
        foreach (var s in new[] { "1", "x", "3" })
            if (p(s, out int n)) bag += n;
        int[] arr = bag.Items.ToArray();
        Console.WriteLine(nameof(List<int>) + " " + bag.Label + " "
            + ((ReadOnlySpan<int>)arr).Total());
    }
}
