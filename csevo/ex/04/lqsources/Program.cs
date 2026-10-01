// 슬라이드 p4-v3-linq-sources — IEnumerable<T> 면 무엇이든, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static void Main()
    {
        string word = "banana";               // IEnumerable<char>
        Console.WriteLine(word.Count(c => c == 'a'));

        Dictionary<string, int> stock = new Dictionary<string, int>();
        stock["pear"] = 3;
        stock["fig"] = 0;
        stock["kiwi"] = 7;
        var inStock = from kv in stock
                      where kv.Value > 0
                      orderby kv.Key       // not the hash order
                      select kv.Key + "=" + kv.Value;
        Console.WriteLine(string.Join(" ", inStock));

        IEnumerable<int> range = Enumerable.Range(1, 5);
        Console.WriteLine(range.Sum() + " "
            + string.Join("", Enumerable.Repeat("ab", 3)));
    }
}
