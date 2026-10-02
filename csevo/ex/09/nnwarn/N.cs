// 슬라이드 p9-v8-notnull-warn — notnull 을 어기면, C# 8.0
#nullable enable
using System;

class R<K> where K : notnull
{
    public string Show(K key) => "[" + key + "]";
}

class App
{
    static void Main()
    {
        var a = new R<string>();
        var b = new R<string?>();       // CS8714
        var c = new R<int?>();          // CS8714
        Console.WriteLine(a.Show("a") + b.Show("b") + c.Show(3));
        Console.WriteLine(b.Show(null!));      // nothing stops it
    }
}
