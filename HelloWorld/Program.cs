using System;

namespace HelloWorld
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("Hello World from Visual Studio 2017!");
            Console.WriteLine("This project was migrated from TFS to GitHub Actions.");
            Console.WriteLine($"Current Date/Time: {DateTime.Now}");
            Console.WriteLine($".NET Framework Version: {Environment.Version}");
            
            Console.WriteLine("\nPress any key to exit...");
            Console.ReadKey();
        }
    }
}