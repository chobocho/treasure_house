// 슬라이드 p6-v5-trap-lazyarg — 인자 검사가 늦게 터진다, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    static async Task<int> LengthAsync(string s)
    {
        if (s == null) throw new ArgumentNullException("s");
        await Task.Delay(1);
        return s.Length;
    }

    // non-async wrapper: checks now, then hands off to the async part
    static Task<int> LengthChecked(string s)
    {
        if (s == null) throw new ArgumentNullException("s");
        return LengthAsync(s);
    }

    static void Main()
    {
        Task<int> t = LengthAsync(null);
        Console.WriteLine("async: call returned, " + t.Status);
        try { LengthChecked(null); }
        catch (ArgumentNullException e)
        {
            Console.WriteLine("wrapper: thrown at the call ("
                + e.ParamName + ")");
        }
    }
}
