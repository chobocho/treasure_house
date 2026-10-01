// 슬라이드 p6-v5-exc-await — 예외는 Task 에 담긴다, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    static async Task<int> Parse(string s)
    {
        await Task.FromResult(0);
        if (s.Length == 0) throw new FormatException("empty");
        return s.Length;
    }

    static async Task<string> Caller(Task<int> t)
    {
        try { return "value " + await t; }
        catch (FormatException e)       // caught as the original type
        {
            return "await threw " + e.GetType().Name + ": " + e.Message;
        }
    }

    static void Main()
    {
        Task<int> t = Parse("");        // does not throw here
        Console.WriteLine("status: " + t.Status);
        Console.WriteLine("t.Exception: " + t.Exception.GetType().Name
            + " -> " + t.Exception.InnerException.GetType().Name);
        Console.WriteLine(Caller(t).Result);
    }
}
