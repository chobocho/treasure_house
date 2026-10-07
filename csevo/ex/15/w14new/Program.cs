// 슬라이드 p15-sum-new — 같은 프로그램의 C# 14 판, C# 14
using System;
using System.Collections.Generic;

delegate bool Parse(string s, out int v);

static class Ext
{
    extension(ReadOnlySpan<int> s)                 // extension block
    {
        public int Total
        {
            get { int t = 0; foreach (int x in s) t += x; return t; }
        }
    }
}

partial class Bag
{
    public partial Bag();                          // partial ctor
    public string Label { get; set => field = value.Trim(); } = "";
    public List<int> Items = new();
    public void operator +=(int x) => Items.Add(x);    // in place
}

partial class Bag
{
    public partial Bag() { }
}

class Program
{
    static void Main()
    {
        Parse p = (s, out v) => int.TryParse(s, out v);  // no types
        Bag bag = new Bag(), none = null;
        bag?.Label = "  fruit ";                   // ?.=
        none?.Label = "x";
        foreach (var s in new[] { "1", "x", "3" })
            if (p(s, out int n)) bag += n;
        int[] arr = bag.Items.ToArray();
        Console.WriteLine(nameof(List<>) + " " + bag.Label + " "
            + arr.Total);                          // array -> span
    }
}
