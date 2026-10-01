// 슬라이드 p2-v1-excwrap — 내 예외 클래스와 InnerException, C# 1.0
using System;

class ConfigException : ApplicationException
{
    public readonly string Key;
    public ConfigException(string key, Exception inner)
        : base("bad config key '" + key + "'", inner)
    {
        Key = key;
    }
}

class App
{
    static int ReadPort(string text)
    {
        try
        {
            return Int32.Parse(text);
        }
        catch (FormatException e)
        {
            throw new ConfigException("port", e);   // wrap, keep cause
        }
    }

    static void Main()
    {
        try { ReadPort("80a"); }
        catch (ConfigException e)
        {
            for (Exception x = e; x != null; x = x.InnerException)
                Console.WriteLine(x.GetType().Name + ": " + x.Message);
            Console.WriteLine("key = " + e.Key);
        }
    }
}
