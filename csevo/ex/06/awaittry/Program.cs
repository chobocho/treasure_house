// 슬라이드 p6-v5-awaittry — try 블록 안의 await, C# 5.0
using System;
using System.Threading.Tasks;

class App
{
    static async Task<int> Fail()
    {
        await Task.Delay(1);
        throw new InvalidOperationException("late failure");
    }

    static async Task<string> Demo()
    {
        string log = "";
        try
        {
            log += "try;";
            await Fail();               // fails after resuming
            log += "not here;";
        }
        catch (InvalidOperationException e)
        {
            log += "catch " + e.Message + ";";
        }
        finally
        {
            log += "finally";
        }
        return log;
    }

    static void Main() { Console.WriteLine(Demo().Result); }
}
