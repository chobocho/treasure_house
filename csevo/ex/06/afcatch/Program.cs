// 슬라이드 p6-v5-after-catch — catch 안의 await 와 다시 던지기, C# 6.0
using System;
using System.Threading.Tasks;

class App
{
    static async Task LogAsync(string s)
    {
        await Task.Yield();
        Console.WriteLine("log: " + s);
    }

    static async Task Work()
    {
        try
        {
            await Task.Yield();
            throw new InvalidOperationException("disk full");
        }
        catch (InvalidOperationException e) when (e.Message != "")
        {
            await LogAsync("caught " + e.Message);
            throw;              // rethrow after an await
        }
        finally
        {
            await LogAsync("finally");
        }
    }

    static void Main()
    {
        try { Work().GetAwaiter().GetResult(); }
        catch (InvalidOperationException e)
        {
            Console.WriteLine("Main got: " + e.Message);
        }
    }
}
