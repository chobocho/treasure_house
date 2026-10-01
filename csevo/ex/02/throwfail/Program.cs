// 슬라이드 p2-v1-throwfail — 던질 수 있는 것은 Exception 뿐, C# 1.0
using System;

class NotAnError { }

class App
{
    static void Main()
    {
        try
        {
            throw new NotAnError();      // not derived from Exception
        }
        catch (NotAnError e)             // same rule for catch
        {
        }
        catch (Exception)
        {
            throw 42;
        }
    }
}
